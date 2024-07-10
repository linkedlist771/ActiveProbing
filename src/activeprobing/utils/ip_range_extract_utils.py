import ipaddress
import json
from tqdm import tqdm
import random
from typing import List, Dict, Iterator
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import cpu_count
from src.activeprobing.configs.path_config import RESOURCES_JSONS_DIR_PATH, RESOURCES_IP_RANGES_DIR_PATH
from src.activeprobing.configs.sdb_configs import (
    TENCENT_CLOUD_IPS_SDB_URL,
    BASE_URL,
    ALIYUN_IPS_SDB_URL,
    HUAWEI_CLOUD_IPS_SDB_URL
)
from src.activeprobing.schemas.vps_ips_schemas import VpsIP


aliyun_ips_json = RESOURCES_JSONS_DIR_PATH / "aliyun_ips_domain_binding_ips.json"
tencent_cloud_ips_json = RESOURCES_JSONS_DIR_PATH / "tencent_cloud_ips_domain_binding_ips.json"
huawei_ips_json = RESOURCES_JSONS_DIR_PATH / "huawei_ips_domain_binding_ips.json"
amazon_ips_json = RESOURCES_JSONS_DIR_PATH / "amazon-ip-ranges.json"

tencent_cloud_ips_save_path = RESOURCES_IP_RANGES_DIR_PATH / "tencent_cloud_ips.jsonl"
aliyun_ips_save_path = RESOURCES_IP_RANGES_DIR_PATH / "aliyun_ips.jsonl"
huawei_ips_save_path = RESOURCES_IP_RANGES_DIR_PATH / "huawei_ips.jsonl"
amazon_ips_save_path = RESOURCES_IP_RANGES_DIR_PATH / "amazon_ips.jsonl"


def process_prefix(prefix: Dict[str, str]) -> Iterator[Dict[str, str]]:
    cidr = prefix["ip_prefix"]
    region = prefix["region"]
    service = prefix["service"]
    network = ipaddress.ip_network(cidr, strict=False)
    ips = random.sample(list(network.hosts()), min(len(list(network.hosts())), 5))
    for ip in ips:
        yield {"ip": str(ip), "region": region, "service": service}

def process_chunk(chunk: list[Dict[str, str]], output_file: str):
    with open(output_file, 'a') as f:
        for prefix in tqdm(chunk, desc="Processing chunk"):
            for ip_data in process_prefix(prefix):
                json.dump(ip_data, f)
                f.write('\n')

def extract_amazon_ips(json_path: str, output_file: str):
    with open(json_path, "r") as f:
        data = json.load(f)

    prefixes = data["prefixes"]
    chunk_size = len(prefixes) // (cpu_count() * 2)  # Adjust chunk size based on CPU count
    chunks = [prefixes[i:i + chunk_size] for i in range(0, len(prefixes), chunk_size)]

    # Clear the output file before starting
    open(output_file, 'w').close()

    with ProcessPoolExecutor() as executor:
        futures = [executor.submit(process_chunk, chunk, output_file) for chunk in chunks]
        for future in tqdm(as_completed(futures), total=len(futures), desc="Processing Amazon prefixes"):
            future.result()  # This is just to ensure all futures complete

    print(f"Extraction complete. Results written to {output_file}")


def extract_sdb_ips(json_path: str, output_file: str, service: str):
    with open(json_path, "r") as f:
        data = json.load(f)
    # yield {"ip": str(ip), "region": region, "service": service}
    ips = []
    for k, v in tqdm(data.items(), desc=f"Processing {service} IPs"):
        for ip in v:
            ips.append({"ip": ip, "region": "", "service": service})
    with open(output_file, 'w') as f:
        for ip_data in ips:
            json.dump(ip_data, f)
            f.write('\n')

def extract_all_sdbs_ips():
    extract_sdb_ips(aliyun_ips_json, aliyun_ips_save_path, "aliyun")
    extract_sdb_ips(tencent_cloud_ips_json, tencent_cloud_ips_save_path, "tencent_cloud")
    extract_sdb_ips(huawei_ips_json, huawei_ips_save_path, "huawei")



if __name__ == "__main__":
    extract_amazon_ips(amazon_ips_json, amazon_ips_save_path)

    # Print the first 5 lines of the output file
    with open(amazon_ips_save_path, 'r') as f:
        for _ in range(5):
            print(f.readline().strip())

    # Print the total number of lines in the file
    with open(amazon_ips_save_path, 'r') as f:
        line_count = sum(1 for _ in f)
    print(f"Total number of IPs extracted: {line_count}")

    extract_all_sdbs_ips()