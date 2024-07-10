import json
from loguru import logger


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
    return ips
