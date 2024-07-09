from loguru import logger
import subprocess


def scan():
    ip = "101.132.169.133"
    logger.info(f"Starting scan for IP: {ip}")

    # 定义要扫描的端口列表
    ports = "80,443,22,21,25,110,143,3389,1433,3306,5432,27017,6379,9200,8080,23,445"

    try:
        # 运行 nmap 命令
        result = subprocess.run(['nmap', '-p', ports, '-T4', ip], capture_output=True, text=True, timeout=300)  # 指定端口
        # result = subprocess.run(['nmap', '-p-', '-T4', ip], capture_output=True, text=True, timeout=3600) # 全部端口扫描


        # 记录输出
        logger.info("Scan results:")
        logger.info(result.stdout)

        # 如果有错误输出，也记录下来
        if result.stderr:
            logger.error(f"Error output: {result.stderr}")

    except subprocess.TimeoutExpired:
        logger.error("Scan timed out after 5 minutes")
    except Exception as e:
        logger.error(f"An error occurred during the scan: {e}")


if __name__ == "__main__":
    logger.add("scan_log.log", rotation="500 MB")
    scan()
