import os


BATCH = int(os.getenv('BATCH', 20))
MAX_PERIOD_SECS = int(os.getenv('MAX_PERIOD_SECS', 86400 * 31))
DATETIME_FORMAT = os.getenv('DATETIME_FORMAT', '%Y%m%dT%H%M%S%z')
DEFAULT_LANGUAGE = os.getenv('DEFAULT_LANGUAGE', 'zh_TW')
# resource probe cycle secs
PROBE_CYCLE_SECS = int(os.getenv("PROBE_CYCLE_SECS", 3))

# default cache ttl: 5 minutes
CACHE_TTL = int(os.getenv('CACHE_TTL', 300))

# db config params
DB_HOST = os.getenv('DB_HOST', 'x-career-db-test.cu7knbzuvltn.ap-northeast-1.rds.amazonaws.com')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')
DB_NAME = os.getenv('DB_NAME', 'postgres')
DB_SCHEMA = os.getenv('DB_SCHEMA', 'x-career-dev')
RESERVATION_ISOLAION_LEVEL = os.getenv('RESERVATION_ISOLAION_LEVEL', 'SERIALIZABLE')

SEARCH_SERVICE_URL = os.getenv('SEARCH_SERVICE_URL', 'http://127.0.0.1:8012/search-service/api')


# sqs/event bus conf
MQ_CONNECT_TIMEOUT = int(os.getenv("MQ_CONNECT_TIMEOUT", 10))
MQ_READ_TIMEOUT = int(os.getenv("MQ_READ_TIMEOUT", 10))
MQ_MAX_ATTEMPTS = int(os.getenv("MQ_MAX_ATTEMPTS", 3))

# sqs
# for retry failed pub events
SQS_QUEUE_URL = os.getenv('SQS_QUEUE_URL', 'https://sqs.{REGION}.amazonaws.com/{ACCOUNT_ID}/{QUEUE_NAME}')
