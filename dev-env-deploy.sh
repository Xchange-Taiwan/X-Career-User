#!/bin/bash

aws lambda update-function-configuration --function-name x-career-user-dev-app --environment --profile xc "Variables={
STAGE=dev,
TESTING=dev,
XC_BUCKET=x-career-bff-dev-serverlessdeploymentbucket-zndkgowobwsz,
BATCH=10,
MAX_PERIOD_SECS=2678400,
DATETIME_FORMAT=%Y-%m-%dT%H:%M:%Z,
DB_HOST=x-career-db-test.cu7knbzuvltn.ap-northeast-1.rds.amazonaws.com,
DB_PORT=5432,
DB_USER=postgres,
DB_PASSWORD=postgres,
DB_NAME=postgres,
DB_SCHEMA=x-career-dev,
CACHE_TTL=300,
}"
