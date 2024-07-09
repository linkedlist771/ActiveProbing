import subprocess
from enum import Enum
from functools import partial
import datetime
from src.activeprobing.configs.ports_config import (
    NORMAL_SERVICE_PORTS,
    NORMAL_SCAN_TIMEOUT,
    FULL_SCAN_TIMEOUT,
)


class ScanType(Enum):
    NORMAL = 0
    FULL = 1


class NmapManger(object):

    def get_scan_command(self):
        if self.scan_type == ScanType.NORMAL:
            return partial(
                subprocess.run,
                ["nmap", "-p", NORMAL_SERVICE_PORTS, "-T4", self.ip],
                capture_output=True,
                text=True,
                timeout=NORMAL_SCAN_TIMEOUT,
            )
        elif self.scan_type == ScanType.FULL:
            return partial(
                subprocess.run,
                ["nmap", "-p-", "-T4", self.ip],
                capture_output=True,
                text=True,
                timeout=FULL_SCAN_TIMEOUT,
            )
        else:
            raise ValueError("Invalid scan type")

    def __init__(self, ip: str, scan_type: ScanType = ScanType.NORMAL):
        self.ip = ip
        self.scan_type = scan_type
        self.scan_command = self.get_scan_command()

    def scan(self):
        return self.scan_command()

    def parse_result(self, result):
        # 解析 nmap 输出
        parsed_result = {
            "ip": self.ip,
            "scan_type": self.scan_type.name,
            "timestamp": datetime.datetime.now().isoformat(),
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode,
        }
        return parsed_result


if __name__ == "__main__":
    ip = "101.132.169.133"
    nmap_manager = NmapManger(ip)
    res = nmap_manager.scan()
    print(res.stdout)
    print(type(res.stdout))
    print(nmap_manager.parse_result(res))
    pass
