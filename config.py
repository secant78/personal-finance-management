import json
import os
import boto3

BOOTSTRAP_FILE = os.path.join(os.path.dirname(__file__), "bootstrap.json")
_cache: dict = {}


def is_setup_complete() -> bool:
    return os.path.exists(BOOTSTRAP_FILE)


def save_bootstrap(aws_access_key_id: str, aws_secret_access_key: str, aws_region: str):
    with open(BOOTSTRAP_FILE, "w") as f:
        json.dump({
            "aws_access_key_id": aws_access_key_id,
            "aws_secret_access_key": aws_secret_access_key,
            "aws_region": aws_region,
        }, f)
    _cache.clear()


def _session() -> boto3.Session:
    with open(BOOTSTRAP_FILE) as f:
        data = json.load(f)
    return boto3.Session(
        aws_access_key_id=data["aws_access_key_id"],
        aws_secret_access_key=data["aws_secret_access_key"],
        region_name=data.get("aws_region", "us-east-1"),
    )


def get(name: str) -> str:
    if name not in _cache:
        ssm = _session().client("ssm")
        _cache[name] = ssm.get_parameter(Name=name, WithDecryption=True)["Parameter"]["Value"]
    return _cache[name]


def put(name: str, value: str):
    ssm = _session().client("ssm")
    ssm.put_parameter(Name=name, Value=value, Type="SecureString", Overwrite=True)
    _cache[name] = value


def clear_cache():
    _cache.clear()
