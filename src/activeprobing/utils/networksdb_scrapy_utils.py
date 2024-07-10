import httpx
import asyncio
import json
import ipaddress
from selectolax.parser import HTMLParser
from loguru import logger
from tqdm import tqdm
from src.activeprobing.configs.path_config import RESOURCES_JSONS_DIR_PATH
from src.activeprobing.configs.sdb_configs import (
    TENCENT_CLOUD_IPS_SDB_URL,
    BASE_URL,
    ALIYUN_IPS_SDB_URL,
    HUAWEI_CLOUD_IPS_SDB_URL
)

def is_valid_ip(ip_string):
    try:
        ipaddress.ip_address(ip_string)
        return True
    except ValueError:
        return False

class SDBWebScraper:
    def __init__(self):
        self.SDB_URLS = [
            TENCENT_CLOUD_IPS_SDB_URL,
            ALIYUN_IPS_SDB_URL,
            HUAWEI_CLOUD_IPS_SDB_URL
        ]
        self.client = httpx.AsyncClient()

    def get_save_path(self, url):
        if url == TENCENT_CLOUD_IPS_SDB_URL:
            return RESOURCES_JSONS_DIR_PATH / "tencent_cloud_ips.json"
        elif url == ALIYUN_IPS_SDB_URL:
            return RESOURCES_JSONS_DIR_PATH / "aliyun_ips.json"
        elif url == HUAWEI_CLOUD_IPS_SDB_URL:
            return RESOURCES_JSONS_DIR_PATH / "huawei_ips.json"
        else:
            raise ValueError("Invalid URL")
    async def scrape_url(self, url):
        response = await self.client.get(url)
        parser = HTMLParser(response.text)
        elements = parser.css('div.row.netblock')
        results = []

        for element in elements:
            info = {}
            # 提取公司信息
            company_info = element.css_first('div.col-md-7')
            if company_info:
                info['company'] = company_info.text(strip=True)

            # 提取网络信息
            network_info = element.css_first('div.col-md-5')
            if network_info:
                for b in network_info.css('b'):
                    key = b.text(strip=True).rstrip(':')
                    value = b.next.text(strip=True) if b.next else ''
                    info[key] = value

                # 提取链接
                links = network_info.css('a')
                info['links'] = [
                    {
                        'text': link.text(strip=True),
                        'href': BASE_URL + link.attributes.get('href', ''),
                        'class': link.attributes.get('class', '')
                    } for link in links
                ]

            results.append(info)

        return results

    async def scrape_domain_binding_url(self, url, max_retries=3, base_delay=1):
        ips = []
        for i in range(max_retries):
            try:
                response = await self.client.get(url)
                parser = HTMLParser(response.text)
                # find all the b tags
                elements = parser.css('b')
                elements_text = [element.text(strip=True).replace(":", "") for element in elements]
                for element in elements_text:
                    if is_valid_ip(element):
                        logger.info(f"找到了 IP 地址：{element}")
                        ips.append(element)
            except Exception as e:
                logger.error(f"获取 {url} 时出错：{e}")
                # 等待一会再请求
                await asyncio.sleep(60)
                if i == max_retries - 1:
                    logger.error(f"无法获取 {url}，跳过")
                    return  []
        return ips


    async def scrape_all(self, urls):
        tasks = [self.scrape_url(url) for url in urls]
        results = await asyncio.gather(*tasks)
        all_results = {

        }
        for url, url_results in zip(self.SDB_URLS, results):
            all_results[url] = url_results
            logger.info(f"从 {url} 提取了 {len(url_results)} 条记录")
        return all_results

    def save_results(self, results):
        for url, url_results in results.items():
            save_path = self.get_save_path(url)
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(url_results, f, ensure_ascii=False, indent=4)
            logger.info(f"保存了 {len(url_results)} 条记录到 {save_path}")

    async def close(self):
        await self.client.aclose()

async def scrapy_sdb():
    scraper = SDBWebScraper()
    try:
        results = await scraper.scrape_all(scraper.SDB_URLS)
        for url, url_results in results.items():
            logger.info(f"从 {url} 提取的信息：\n{json.dumps(url_results, indent=4, ensure_ascii=False)}")

        # 保存结果到 JSON 文件
        scraper.save_results(results)
    finally:
        await scraper.close()


async def scrapy_sdb_domain_binding_ips():
    tencent_cloud_ips_json = RESOURCES_JSONS_DIR_PATH / "tencent_cloud_ips.json"
    aliyun_ips_json = RESOURCES_JSONS_DIR_PATH / "aliyun_ips.json"
    huawei_ips_json = RESOURCES_JSONS_DIR_PATH / "huawei_ips.json"
    ips_jsons = [tencent_cloud_ips_json, aliyun_ips_json, huawei_ips_json]
    scanner = SDBWebScraper()  # 每秒10个请求的限制

    all_domain_binding_ips = {}

    async def process_ip_json(ip_json):
        ips = json.loads(ip_json.read_text())
        links = [ip['links'] for ip in ips]
        domain_links = [link[1]["href"] for link in links]
        logger.info(f"从 {ip_json} 读取了 {len(domain_links)} 条记录")

        async def process_url(url):
            ips = await scanner.scrape_domain_binding_url(url)
            return url, ips

        tasks = [process_url(url) for url in domain_links]
        results = await asyncio.gather(*tasks)

        domain_binding_ips = dict(results)

        # Save domain binding IPs for each cloud provider
        save_path = RESOURCES_JSONS_DIR_PATH / f"{ip_json.stem}_domain_binding_ips.json"
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(domain_binding_ips, f, ensure_ascii=False, indent=4)
        logger.info(f"保存了 {len(domain_binding_ips)} 条域名绑定 IP 记录到 {save_path}")

        return ip_json.stem, domain_binding_ips

    try:
        results = await asyncio.gather(*[process_ip_json(ip_json) for ip_json in ips_jsons])

        for stem, domain_binding_ips in results:
            all_domain_binding_ips[stem] = domain_binding_ips

        # Save all domain binding IPs
        all_save_path = RESOURCES_JSONS_DIR_PATH / "all_domain_binding_ips.json"
        with open(all_save_path, 'w', encoding='utf-8') as f:
            json.dump(all_domain_binding_ips, f, ensure_ascii=False, indent=4)
        logger.info(f"保存了所有域名绑定 IP 记录到 {all_save_path}")

    finally:
        await scanner.close()

async def main():
    # await scrapy_sdb()
    await scrapy_sdb_domain_binding_ips()

if __name__ == "__main__":
    asyncio.run(main())
