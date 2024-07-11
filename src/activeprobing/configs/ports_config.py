ALL_SERVICE_PORTS = [
    # 原有的常用端口
    80,
    443,
    22,
    21,
    25,
    110,
    143,
    3389,
    1433,
    3306,
    5432,
    27017,
    6379,
    9200,
    8080,
    23,
    445,
    # Web 服务
    8000,
    8443,
    9000,
    # 邮件服务
    587,
    993,
    995,
    # 文件传输
    20,
    989,
    990,
    # 远程访问
    5900,
    5901,
    5902,
    5903,
    5904,
    5905,
    22222,  # 5900-5999 范围，这里只列举了几个
    # 数据库
    5433,
    1521,
    1830,
    # 消息队列
    5672,
    61613,
    1883,
    # 版本控制
    9418,
    3690,
    # 其他服务
    53,
    123,
    161,
    389,
    636,
    2049,
    5353,
    11211,
]

NORMAL_SERVICE_PORTS_LIST = [str(port) for port in sorted(set(ALL_SERVICE_PORTS))]
# 将列表排序并去重
NORMAL_SERVICE_PORTS = ",".join(NORMAL_SERVICE_PORTS_LIST)

NORMAL_SCAN_TIMEOUT = 300

FULL_SCAN_TIMEOUT = 3600
