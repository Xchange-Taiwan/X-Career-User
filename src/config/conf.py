import os


XC_BUCKET = os.getenv('XC_BUCKET', 'xc-bucket')
XC_USER_BUCKET = os.getenv('XC_USER_BUCKET', 'xc-user-bucket')
BATCH = int(os.getenv('BATCH', 20))
MAX_PERIOD_SECS = int(os.getenv('MAX_PERIOD_SECS', 86400 * 31))
DATETIME_FORMAT = os.getenv('DATETIME_FORMAT', '%Y%m%dT%H%M%S%z')
DEFAULT_LANGUAGE = os.getenv('DEFAULT_LANGUAGE', 'zh_TW')
# resource probe cycle secs
PROBE_CYCLE_SECS = int(os.getenv("PROBE_CYCLE_SECS", 3))

# default cache ttl: 5 minutes
CACHE_TTL = int(os.getenv('CACHE_TTL', 300))

# db config params
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')
DB_NAME = os.getenv('DB_NAME', 'postgres')
DB_SCHEMA = os.getenv('DB_SCHEMA', 'x-career-dev')
RESERVATION_ISOLAION_LEVEL = os.getenv('RESERVATION_ISOLAION_LEVEL', 'SERIALIZABLE')

# db connection pool config params
# 資料庫連接池配置 - 可通過環境變量覆蓋默認值
DB_POOL_SIZE = int(os.getenv('DB_POOL_SIZE', 20))           # 連接池大小 (建議: 10-50)
DB_MAX_OVERFLOW = int(os.getenv('DB_MAX_OVERFLOW', 4))      # 最大溢出連接數 (建議: 0-10)
DB_POOL_TIMEOUT = int(os.getenv('DB_POOL_TIMEOUT', 30))     # 獲取連接的超時時間（秒, 建議: 10-60）
DB_POOL_RECYCLE = int(os.getenv('DB_POOL_RECYCLE', 3600))   # 連接回收時間（秒, 建議: 3600-7200）
DB_POOL_PRE_PING = int(os.getenv('DB_POOL_PRE_PING', 1))    # 連接前先 ping 檢查連接是否有效
DB_POOL_PRE_PING = True if DB_POOL_PRE_PING >= 1 else False

DB_COMMAND_TIMEOUT = int(os.getenv('DB_COMMAND_TIMEOUT', 60))   # 命令超時時間（秒, 建議: 30-300）
DB_JIT_OFF = int(os.getenv('DB_JIT_OFF', 1))    # 是否關閉 PostgreSQL JIT (提高穩定性)
DB_JIT_OFF = True if DB_JIT_OFF >= 1 else False

SEARCH_SERVICE_URL = os.getenv('SEARCH_SERVICE_URL', 'http://127.0.0.1:8012/search-service/api')


# sqs/event bus conf
MQ_CONNECT_TIMEOUT = int(os.getenv("MQ_CONNECT_TIMEOUT", 10))
MQ_READ_TIMEOUT = int(os.getenv("MQ_READ_TIMEOUT", 10))
MQ_MAX_ATTEMPTS = int(os.getenv("MQ_MAX_ATTEMPTS", 3))

# sqs
# for retry failed pub events
SQS_QUEUE_URL = os.getenv('SQS_QUEUE_URL', 'https://sqs.{REGION}.amazonaws.com/{ACCOUNT_ID}/{QUEUE_NAME}')
