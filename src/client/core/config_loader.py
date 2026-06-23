"""
VLK Launcher — Remote config loader
Fetches config.json from GitHub on startup, falls back to local copy.
GitHub raw URL: https://raw.githubusercontent.com/yo-le-zz/VLK-Team-Launcheur/main/config.json
"""
import json
import os
import sys
import threading
import requests

GITHUB_CONFIG_URL = "https://raw.githubusercontent.com/yo-le-zz/VLK-Team-Launcheur/main/config.json"
LOCAL_FALLBACK = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config.json")

_DEFAULT = {
    "server_url": os.environ.get("VLK_SERVER_URL", "http://localhost:8000"),
    "clan_name": "VOLKZ CLAN",
    "clan_tag": "VLK",
    "game": "Rivals",
    "version": "1.0.0",
    "voice_enabled": True,
    "voice_sample_rate": 48000,
    "voice_channels": 1,
    "voice_chunk_ms": 20,
    "maintenance": False,
    "maintenance_message": "",
}

_config: dict = dict(_DEFAULT)
_loaded = threading.Event()


def load_config(timeout: float = 5.0) -> dict:
    """Fetch config from GitHub. Falls back to local then default."""
    global _config
    try:
        resp = requests.get(GITHUB_CONFIG_URL, timeout=timeout)
        resp.raise_for_status()
        remote = resp.json()
        _config = {**_DEFAULT, **remote}
        print(f"[Config] Loaded from GitHub: server_url={_config['server_url']}")
    except Exception as e:
        print(f"[Config] GitHub fetch failed ({e}), trying local fallback...")
        try:
            with open(LOCAL_FALLBACK, "r") as f:
                local = json.load(f)
            _config = {**_DEFAULT, **local}
            print(f"[Config] Loaded from local: server_url={_config['server_url']}")
        except Exception as e2:
            print(f"[Config] Local fallback failed ({e2}), using defaults.")
            _config = dict(_DEFAULT)
    _loaded.set()
    return _config


def get(key: str, default=None):
    """Get a config value (loads synchronously if not yet loaded)."""
    if not _loaded.is_set():
        load_config()
    return _config.get(key, default)


def get_server_url() -> str:
    return get("server_url", "http://localhost:8000")


def get_clan_name() -> str:
    return get("clan_name", "VOLKZ CLAN")


def is_maintenance() -> bool:
    return bool(get("maintenance", False))


def get_all() -> dict:
    if not _loaded.is_set():
        load_config()
    return dict(_config)
