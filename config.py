import base64
import json
import os
import subprocess

BOOTSTRAP_FILE = os.path.join(os.path.dirname(__file__), "bootstrap.json")
_cache: dict = {}
_session_key: str | None = None


def is_setup_complete() -> bool:
    return os.path.exists(BOOTSTRAP_FILE)


def save_bootstrap(vaultwarden_url: str, bw_client_id: str, bw_client_secret: str, bw_password: str):
    with open(BOOTSTRAP_FILE, "w") as f:
        json.dump({
            "vaultwarden_url": vaultwarden_url,
            "bw_client_id": bw_client_id,
            "bw_client_secret": bw_client_secret,
            "bw_password": bw_password,
        }, f)
    global _session_key
    _session_key = None
    _cache.clear()


def _get_session() -> str:
    global _session_key
    if _session_key:
        return _session_key

    with open(BOOTSTRAP_FILE) as f:
        data = json.load(f)

    env = {
        **os.environ,
        "BW_CLIENTID": data["bw_client_id"],
        "BW_CLIENTSECRET": data["bw_client_secret"],
        "BW_PASSWORD": data["bw_password"],
    }

    url = data["vaultwarden_url"].rstrip("/")
    if url in ("https://bitwarden.com", "https://vault.bitwarden.com", "bitwarden.com", ""):
        # Reset to hosted Bitwarden defaults (correct API subdomain routing)
        subprocess.run(["bw", "config", "server", "bitwarden.com"],
                       capture_output=True, env=env)
    else:
        subprocess.run(["bw", "config", "server", url],
                       capture_output=True, env=env, check=True)

    # Check current login status
    status_result = subprocess.run(
        ["bw", "status"], capture_output=True, text=True, env=env
    )
    try:
        status = json.loads(status_result.stdout).get("status", "unauthenticated")
    except Exception:
        status = "unauthenticated"

    if status == "unauthenticated":
        login_result = subprocess.run(
            ["bw", "login", "--apikey"],
            capture_output=True, text=True, env=env,
        )
        if login_result.returncode != 0:
            raise RuntimeError(f"Bitwarden login failed: {login_result.stderr.strip() or login_result.stdout.strip()}")

    result = subprocess.run(
        ["bw", "unlock", "--passwordenv", "BW_PASSWORD", "--raw"],
        capture_output=True, text=True, env=env,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Bitwarden unlock failed: {result.stderr.strip() or result.stdout.strip()}")

    _session_key = result.stdout.strip()
    return _session_key


def _bw(args: list[str]) -> str:
    env = {**os.environ, "BW_SESSION": _get_session()}
    result = subprocess.run(["bw"] + args, capture_output=True, text=True, env=env, check=True)
    return result.stdout.strip()


def _encode(item: dict) -> str:
    return base64.b64encode(json.dumps(item).encode()).decode()


def get(name: str) -> str:
    if name not in _cache:
        items = json.loads(_bw(["list", "items", "--search", name]))
        match = next((i for i in items if i["name"] == name), None)
        if match is None:
            raise KeyError(f"Secret '{name}' not found in Vaultwarden")
        _cache[name] = match.get("notes") or ""
    return _cache[name]


def put(name: str, value: str):
    items = json.loads(_bw(["list", "items", "--search", name]))
    existing = next((i for i in items if i["name"] == name), None)

    if existing:
        existing["notes"] = value
        _bw(["edit", "item", existing["id"], _encode(existing)])
    else:
        template = json.loads(_bw(["get", "template", "item"]))
        template.update({"type": 2, "name": name, "notes": value, "secureNote": {"type": 0}})
        for key in ["login", "card", "identity", "fields"]:
            template.pop(key, None)
        _bw(["create", "item", _encode(template)])

    _cache[name] = value


def clear_cache():
    global _session_key
    _session_key = None
    _cache.clear()
