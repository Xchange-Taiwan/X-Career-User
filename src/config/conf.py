import os


# schedule
SCHEDULE_YEAR = int(os.getenv('SCHEDULE_YEAR', '-1'))
SCHEDULE_MONTH = int(os.getenv('SCHEDULE_MONTH', '-1'))
SCHEDULE_DAY_OF_MONTH = int(os.getenv('SCHEDULE_DAY_OF_MONTH', '-1'))
SCHEDULE_DAY_OF_WEEK = int(os.getenv('SCHEDULE_DAY_OF_WEEK', '-1'))

BATCH = int(os.getenv('BATCH', 20))
MAX_PERIOD_SECS = int(os.getenv('MAX_PERIOD_SECS', 86400 * 31))
DATETIME_FORMAT = os.getenv('DATETIME_FORMAT', '%Y%m%dT%H%M%S%z')

# default cache ttl: 5 minutes
CACHE_TTL = int(os.getenv('CACHE_TTL', 300))

# db config params
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_USER = os.getenv('DB_USER', 'user_connection')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'pg_user_password')
DB_NAME = os.getenv('DB_NAME', 'x-career')
DB_SCHEMA = os.getenv('DB_SCHEMA', 'Xchange_local')

RESERVATION_ISOLAION_LEVEL = os.getenv('RESERVATION_ISOLAION_LEVEL', 'SERIALIZABLE')
