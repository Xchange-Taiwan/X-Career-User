import os

BATCH = int(os.getenv('BATCH', '10'))

# schedule
SCHEDULE_YEAR = int(os.getenv('SCHEDULE_YEAR', '-1'))
SCHEDULE_MONTH = int(os.getenv('SCHEDULE_MONTH', '-1'))
SCHEDULE_DAY_OF_MONTH = int(os.getenv('SCHEDULE_DAY_OF_MONTH', '-1'))
SCHEDULE_DAY_OF_WEEK = int(os.getenv('SCHEDULE_DAY_OF_WEEK', '-1'))

DB_URL = os.getenv('DB_URL', 'postgresql+asyncpg://postgres:postgres@x-career-db-test.cu7knbzuvltn.ap-northeast-1.rds.amazonaws.com:5432/postgres')
