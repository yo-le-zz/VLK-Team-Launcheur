"""
VLK Launcher — Remote config loader
Fetches config.json from GitHub on startup, falls back to local copy.
Saves a disk cache so subsequent launches are instant.
GitHub raw URL: https://raw.githubusercontent.com/yo-le-zz/VLK-Team-Launcheur/main/config.json
"""
import json
import os
import sys
import threading
import requests

GITHUB_CONFIG_URL = "https://raw.githubusercontent.com/yo-le-zz/VLK-Team-Launcheur/main/config.json"

# Locate paths regardless of whether we're frozen (PyInstaller) or running from source
if getattr(sys, "frozen", False):
    _BASE = os.path.dirname(sys.executable)
else:
    _BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

LOCAL_FALLBACK = os.path.join(_BASE, "config.json")
CACHE_PATH = os.path.join(_BASE, ".vlk_config_cache.json")

_DEFAULT: dict = {
    "server_url": os.environ.get("VLK_SERVER_URL", "http://localhost:8000"),
    "clan_name": "VOLKZ CLAN",
    "clan_tag": "VLK",
    "game": "Rivals",
    "game_place_id": "17017769292",
    "roblox_url": "roblox://placeId=17017769292",
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


def _save_cache(cfg: dict) -> None:
    """Persist config to disk so next launch is instant."""
    try:
        with open(CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except Exception:
        pass


def _load_cache() -> dict | None:
    """Return cached config if available, else None."""
    try:
        if os.path.exists(CACHE_PATH):
            with open(CACHE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return None


def load_config(timeout: float = 4.0) -> dict:
    """
    Load config with this priority:
    1. Disk cache (instant, avoids slow network on every start)
    2. GitHub remote (background refresh — updates cache for next launch)
    3. Local config.json bundled with the app
    4. Built-in _DEFAULT dict

    The function returns immediately after loading from cache; the GitHub
    refresh happens in the background so it never blocks the splash screen.
    """
    global _config

    # ── Step 1: serve from cache immediately ─────────────────────────────────
    cached = _load_cache()
    if cached:
        _config = {**_DEFAULT, **cached}
        print(f"[Config] Loaded from cache: server_url={_config['server_url']}")
        _loaded.set()
        # Refresh from GitHub in background so cache stays fresh
        threading.Thread(target=_background_refresh, daemon=True).start()
        return _config

    # ── Step 2: no cache — try GitHub synchronously (first launch) ───────────
    try:
        resp = requests.get(GITHUB_CONFIG_URL, timeout=timeout)
        resp.raise_for_status()
        remote = resp.json()
        _config = {**_DEFAULT, **remote}
        _save_cache(_config)
        print(f"[Config] Loaded from GitHub: server_url={_config['server_url']}")
        _loaded.set()
        return _config
    except Exception as e:
        print(f"[Config] GitHub fetch failed ({e}), trying local fallback...")

    # ── Step 3: local config.json ─────────────────────────────────────────────
    try:
        with open(LOCAL_FALLBACK, "r", encoding="utf-8") as f:
            local = json.load(f)
        _config = {**_DEFAULT, **local}
        _save_cache(_config)
        print(f"[Config] Loaded from local file: server_url={_config['server_url']}")
        _loaded.set()
        return _config
    except Exception as e2:
        print(f"[Config] Local fallback failed ({e2}), using built-in defaults.")

    # ── Step 4: built-in defaults ─────────────────────────────────────────────
    _config = dict(_DEFAULT)
    _loaded.set()
    return _config


def _background_refresh() -> None:
    """Silently refresh config from GitHub and update cache (no UI side effects)."""
    global _config
    try:
        resp = requests.get(GITHUB_CONFIG_URL, timeout=6)
        resp.raise_for_status()
        remote = resp.json()
        _config = {**_DEFAULT, **remote}
        _save_cache(_config)
        print(f"[Config] Background refresh OK: server_url={_config['server_url']}")
    except Exception as e:
        print(f"[Config] Background refresh failed: {e}")


# ── Accessors ─────────────────────────────────────────────────────────────────

def get(key: str, default=None):
    if not _loaded.is_set():
        load_config()
    return _config.get(key, default)


def get_server_url() -> str:
    return get("server_url", "http://localhost:8000")


def get_clan_name() -> str:
    return get("clan_name", "VOLKZ CLAN")


def get_roblox_url() -> str:
    return get("roblox_url", f"roblox://placeId={get('game_place_id', '17017769292')}")


def is_maintenance() -> bool:
    return bool(get("maintenance", False))


def get_all() -> dict:
    if not _loaded.is_set():
        load_config()
    return dict(_config)
