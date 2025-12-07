import json
import os

import boto3
import openai

YANDEX_KEY_ID = os.environ.get("YANDEX_KEY_ID")
YANDEX_KEY_SECRET = os.environ.get("YANDEX_KEY_SECRET")
YANDEX_BUCKET = os.environ.get("YANDEX_BUCKET")
PROXY_API_KEY = os.environ.get("PROXY_API_KEY")
ASSISTANT_MODEL = os.environ.get("ASSISTANT_MODEL")
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN")
TG_BOT_ADMIN = os.environ.get("TG_BOT_ADMIN")


def get_s3_client():
    session = boto3.session.Session(
        aws_access_key_id=YANDEX_KEY_ID, aws_secret_access_key=YANDEX_KEY_SECRET
    )
    return session.client(
        service_name="s3", endpoint_url="https://storage.yandexcloud.net"
    )


def get_config() -> dict:
    s3client = get_s3_client()
    try:
        response = s3client.get_object(Bucket=YANDEX_BUCKET, Key="config.json")
        return json.loads(response["Body"].read())
    except:
        return {}


def save_config(new_config: dict):
    s3client = get_s3_client()
    s3client.put_object(
        Bucket=YANDEX_BUCKET, Key="config.json", Body=json.dumps(new_config)
    )


proxy_client = openai.Client(
    api_key=PROXY_API_KEY,
    base_url="https://api.proxyapi.ru/openai/v1",
)