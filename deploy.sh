#!/bin/bash

# 默认环境文件
ENV_FILE=".env"
SERVERLESS_FILE="serverless.yml"
BACKUP_ENV="UNKNOW_ENV!!!"  # 环境尚未指定 (一定要在 CLI 指定)
BACKUP_FILE="serverless.$BACKUP_ENV.yml"  # 设置备份文件名

# 取得 AWS 帳號 region
REGION=$(aws configure get region)
# 取得 AWS 帳號別名，默認為 "default"
AWS_PROFILE="default"

# 解析命令行选项
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -e|--env) ENV_FILE="$ENV_FILE.$2"; BACKUP_ENV="$2"; BACKUP_FILE="serverless.$BACKUP_ENV.yml"; shift ;;  # 指定环境文件
        -r|--region) REGION="$2"; shift ;;  # 指定区域
        -a|--account) AWS_PROFILE="$2"; REGION=$(aws configure get region --profile "$2"); shift ;; # 指定 AWS 帳號；重新取得該帳號 region
        *) echo "未知选项: $1"; exit 1 ;;  # 处理未知选项
    esac
    shift
done

# 检查环境文件是否存在
if [ ! -f "$ENV_FILE" ]; then
    echo "$ENV_FILE 文件不存在"
    exit 1
fi

cp $SERVERLESS_FILE $BACKUP_FILE

# 替换 ${env:STAGE} 和 ${env:THE_REGION}
sed -i.bak "s|\${env:STAGE}|$BACKUP_ENV|g" "$BACKUP_FILE"  # 替换环境
sed -i.bak "s|\${env:THE_REGION}|$REGION|g" "$BACKUP_FILE"  # 替换区域

# 读取 .env.dev 文件并替换 serverless.yml 中的环境变量
while IFS='=' read -r key value; do
    # 跳过空行和注释行
    if [[ ! -z "$key" && ! "$key" =~ ^# ]]; then
        # 使用 sed 替换 serverless.yml 中的环境变量
        sed -i.bak "s|\${env:$key}|$value|g" "$BACKUP_FILE"
    fi
done < "$ENV_FILE"

# 将备份文件重命名为 serverless.$BACKUP_ENV.yml
rm "$BACKUP_FILE.bak"

echo "替换完成，备份文件为 $BACKUP_FILE"


# 若有兩個以上的 AWS 帳號，需設定帳號別名
export AWS_PROFILE=$AWS_PROFILE

# deploy
sls print --config $BACKUP_FILE --region $REGION --stage $BACKUP_ENV # 添加区域和环境参数
sls deploy --config $BACKUP_FILE --region $REGION --stage $BACKUP_ENV # 添加区域和环境参数
rm "$BACKUP_FILE"


if [ -f "$BACKUP_ENV-env-deploy.sh" ]; then
    echo "Deploying env params..."
    bash $BACKUP_ENV-env-deploy.sh
fi
