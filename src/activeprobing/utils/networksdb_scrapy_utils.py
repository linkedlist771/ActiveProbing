import httpx
import asyncio
import json
from selectolax.parser import HTMLParser
from loguru import logger

from src.activeprobing.configs.path_config import RESOURCES_JSONS_DIR_PATH
from src.activeprobing.configs.sdb_configs import (
    TENCENT_CLOUD_IPS_SDB_URL,
    BASE_URL,
    ALIYUN_IPS_SDB_URL,
    HUAWEI_CLOUD_IPS_SDB_URL
)


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

    async def scrape_all(self):
        tasks = [self.scrape_url(url) for url in self.SDB_URLS]
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


async def main():
    scraper = SDBWebScraper()
    try:
        results = await scraper.scrape_all()
        for url, url_results in results.items():
            logger.info(f"从 {url} 提取的信息：\n{json.dumps(url_results, indent=4, ensure_ascii=False)}")

        # 保存结果到 JSON 文件
        scraper.save_results(results)
    finally:
        await scraper.close()


if __name__ == "__main__":
    asyncio.run(main())
