import os


# schedule
SCHEDULE_YEAR = int(os.getenv('SCHEDULE_YEAR', '-1'))
SCHEDULE_MONTH = int(os.getenv('SCHEDULE_MONTH', '-1'))
SCHEDULE_DAY_OF_MONTH = int(os.getenv('SCHEDULE_DAY_OF_MONTH', '-1'))
SCHEDULE_DAY_OF_WEEK = int(os.getenv('SCHEDULE_DAY_OF_WEEK', '-1'))

BATCH = int(os.getenv('BATCH', 20))
MAX_PERIOD_SECS = int(os.getenv('MAX_PERIOD_SECS', 86400 * 31))
DATETIME_FORMAT = os.getenv('DATETIME_FORMAT', '%Y%m%dT%H%M%S%z')
DEFAULT_LANGUAGE = os.getenv('DEFAULT_LANGUAGE', 'zh_TW')

# db config params
DB_HOST = os.getenv('DB_HOST', 'x-career-db-test.cu7knbzuvltn.ap-northeast-1.rds.amazonaws.com')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')
DB_NAME = os.getenv('DB_NAME', 'postgres')
DB_SCHEMA = os.getenv('DB_SCHEMA', 'x-career-dev')

# default cache ttl: 5 minutes
CACHE_TTL = int(os.getenv('CACHE_TTL', 300))

SEARCH_SERVICE_URL = os.getenv('SEARCH_SERVICE_URL', 'https://76mn9fb6r8.execute-api.ap-northeast-1.amazonaws.com/dev/search-service/api')
