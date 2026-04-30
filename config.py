import boto3
from functools import lru_cache

_ssm = None

def _client():
    global _ssm
    if _ssm is None:
        _ssm = boto3.client("ssm", region_name="us-east-1")
    return _ssm

@lru_cache(maxsize=None)
def get(name: str) -> str:
    """Fetch a SecureString parameter from AWS Parameter Store (cached per process)."""
    response = _client().get_parameter(Name=name, WithDecryption=True)
    return response["Parameter"]["Value"]
