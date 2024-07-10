from os import cpu_count

from loguru import logger
import json
from multiprocessing import Lock, Pool, Manager
from tqdm import tqdm
import time
from typing import Dict
from src.activeprobing.configs.path_config import (
    RESOURCES_NMAP_SCAN_RES_DIR_PATH,
    RESOURCES_IP_RANGES_DIR_PATH,
)
from src.activeprobing.utils.json_utils import load_ips
from src.activeprobing.utils.umap_utils import NmapManger

logger.add("scan_log.log")

aliyun_ips_range_path = RESOURCES_IP_RANGES_DIR_PATH / "aliyun_ips.jsonl"
huawei_ips_range_path = RESOURCES_IP_RANGES_DIR_PATH / "huawei_ips.jsonl"
amazon_ips_range_path = RESOURCES_IP_RANGES_DIR_PATH / "amazon_ips.jsonl"
tencent_cloud_ips_save_path = RESOURCES_IP_RANGES_DIR_PATH / "tencent_cloud_ips.jsonl"

aliyun_scan_res_path = RESOURCES_NMAP_SCAN_RES_DIR_PATH / "aliyun_scan_res.jsonl"
huawei_scan_res_path = RESOURCES_NMAP_SCAN_RES_DIR_PATH / "huawei_scan_res.jsonl"
amazon_scan_res_path = RESOURCES_NMAP_SCAN_RES_DIR_PATH / "amazon_scan_res.jsonl"
tencent_cloud_scan_res_path = (
    RESOURCES_NMAP_SCAN_RES_DIR_PATH / "tencent_cloud_scan_res.jsonl"
)


def process_chunk(chunk: list[Dict[str, str]], output_file: str, lock: Lock):
    results = []
    for ip in tqdm(chunk, desc="Processing chunk"):
        nmap_manager = NmapManger(ip)
        res = nmap_manager.scan(json_res=True)
        results.append(res)

    with lock:
        with open(output_file, "a") as f:
            for ip_data in results:
                ip_data_str = json.dumps(ip_data)
                f.write(ip_data_str)
                f.write("\n")


def scan_ips(ips: list[Dict[str, str]], output_file: str, num_processes: int = 4):
    chunk_size = max(len(ips) // num_processes, 1)

    chunks = [ips[i : i + chunk_size] for i in range(0, len(ips), chunk_size)]

    with Manager() as manager:
        lock = manager.Lock()
        with Pool(processes=num_processes) as pool:
            pool.starmap(
                process_chunk, [(chunk, output_file, lock) for chunk in chunks]
            )


def main():
    idx = -1
    start_time = time.time()
    # Load IP ranges for each cloud provider
    aliyun_ips = load_ips(aliyun_ips_range_path)[:idx]
    huawei_ips = load_ips(huawei_ips_range_path)[:idx]
    amazon_ips = load_ips(amazon_ips_range_path)[:idx]
    tencent_cloud_ips = load_ips(tencent_cloud_ips_save_path)[:idx]

    # Log information about loaded IPs
    for provider, ips in tqdm(
        [
            ("Aliyun", aliyun_ips),
            ("Huawei", huawei_ips),
            ("Amazon", amazon_ips),
            ("Tencent Cloud", tencent_cloud_ips),
        ],
        desc="Loading IPs",
    ):
        logger.info(f"{provider} IPs: {ips[:5]}...")  # Show first 5 IPs
        logger.info(f"{provider} IPs count: {len(ips)}")

    # Scan IPs for each cloud provider
    providers = [
        ("Aliyun", aliyun_ips, aliyun_scan_res_path),
        ("Huawei", huawei_ips, huawei_scan_res_path),
        ("Amazon", amazon_ips, amazon_scan_res_path),
        ("Tencent Cloud", tencent_cloud_ips, tencent_cloud_scan_res_path),
    ]

    # 使用tqdm创建一个总进度条
    with tqdm(total=len(providers), desc="Overall scanning progress") as pbar:
        for provider, ips, scan_res_path in providers:
            logger.info(f"Starting {provider} IP scan")
            scan_ips(ips, scan_res_path, num_processes=cpu_count())
            pbar.update(1)
            pbar.set_description(f"Completed {provider} scan")

    logger.info("All scans completed")
    time_elapsed = time.time() - start_time
    logger.info(f"Time elapsed: {time_elapsed:.2f} seconds")


if __name__ == "__main__":
    main()
