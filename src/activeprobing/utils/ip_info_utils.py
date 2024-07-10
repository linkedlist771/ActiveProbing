import asyncio
import httpx
import folium
from folium.plugins import HeatMap
from loguru import logger
from tqdm.asyncio import tqdm
import json
import os
import random
from src.activeprobing.configs.path_config import (
    RESOURCES_IP_RANGES_DIR_PATH,
    RESOURCES_IP_RANGES_DIR_PATH,
)

IPCOUNTS = 100


def load_ips(file_path):
    ips = []
    with open(file_path, "r") as f:
        for line in f:
            try:
                data = json.loads(line.strip())
                if "ip" in data:
                    ips.append(data["ip"])
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding JSON in line: {line}. Error: {str(e)}")
    ips = random.sample(ips, min(len(ips), IPCOUNTS))
    return ips


async def get_ip_location(client, ip):
    try:
        response = await client.get(f"https://ipapi.co/{ip}/json/")
        data = response.json()
        logger.info(f"IP: {ip}, Location: {data}")
        return {
            "ip": ip,
            "latitude": data.get("latitude"),
            "longitude": data.get("longitude"),
            "city": data.get("city"),
            "country": data.get("country_name"),
        }
    except Exception as e:
        logger.error(f"Error fetching location for IP {ip}: {str(e)}")
        return None


def create_heatmap(ip_locations, filename):
    m = folium.Map(location=[30, 0], zoom_start=2)
    heat_data = [[loc["latitude"], loc["longitude"]] for loc in ip_locations if loc]
    HeatMap(heat_data).add_to(m)
    m.save(filename)


async def process_ip_list(ip_list, provider_name):
    async with httpx.AsyncClient() as client:
        tasks = [get_ip_location(client, ip) for ip in ip_list]
        ip_locations = await tqdm.gather(*tasks, desc=f"获取{provider_name}IP位置")

    ip_locations = [loc for loc in ip_locations if loc]  # 过滤掉None值
    create_heatmap(ip_locations, f"{provider_name}_heatmap.html")
    return ip_locations


async def main():
    # 加载各云服务提供商的IP
    tencent_ips = load_ips(RESOURCES_IP_RANGES_DIR_PATH / "tencent_cloud_ips.jsonl")
    aliyun_ips = load_ips(RESOURCES_IP_RANGES_DIR_PATH / "aliyun_ips.jsonl")
    huawei_ips = load_ips(RESOURCES_IP_RANGES_DIR_PATH / "huawei_ips.jsonl")
    amazon_ips = load_ips(RESOURCES_IP_RANGES_DIR_PATH / "amazon_ips.jsonl")

    # 异步处理每个云服务提供商的IP

    tencent_locations = await process_ip_list(tencent_ips, "tencent")
    aliyun_locations = await process_ip_list(aliyun_ips, "aliyun")
    huawei_locations = await process_ip_list(huawei_ips, "huawei")
    amazon_locations = await process_ip_list(amazon_ips, "amazon")

    # 创建综合热图
    all_locations = (
        tencent_locations + aliyun_locations + huawei_locations + amazon_locations
    )
    create_heatmap(all_locations, "../../../resources/htmls/all_providers_heatmap.html")


if __name__ == "__main__":
    asyncio.run(main())
