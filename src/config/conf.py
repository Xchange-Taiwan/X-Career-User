import os


BATCH = int(os.getenv('BATCH', 20))
MAX_PERIOD_SECS = int(os.getenv('MAX_PERIOD_SECS', 86400 * 31))
DATETIME_FORMAT = os.getenv('DATETIME_FORMAT', '%Y%m%dT%H%M%S%z')

# db config params
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_USER = os.getenv('DB_USER', 'user_connection')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'pg_user_password')
DB_NAME = os.getenv('DB_NAME', 'x-career')
DB_SCHEMA = os.getenv('DB_SCHEMA', 'Xchange_local')
