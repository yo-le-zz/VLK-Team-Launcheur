"""VLK Launcher — HTTP + WebSocket client core"""
import json
import asyncio
import threading
import requests
from typing import Callable, Optional

class VLKApiClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self.token: Optional[str] = None
        self.user: Optional[dict] = None
        self._ws = None
        self._ws_thread: Optional[threading.Thread] = None
        self._ws_callbacks: dict[str, list[Callable]] = {}
        self._running = False

    def _headers(self) -> dict:
        h = {"Content-Type": "application/json"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def _post(self, path: str, data: dict) -> dict:
        r = requests.post(f"{self.base_url}{path}", json=data, headers=self._headers(), timeout=10)
        r.raise_for_status()
        return r.json()

    def _get(self, path: str) -> dict | list:
        r = requests.get(f"{self.base_url}{path}", headers=self._headers(), timeout=10)
        r.raise_for_status()
        return r.json()

    def _patch(self, path: str, data: dict) -> dict:
        r = requests.patch(f"{self.base_url}{path}", json=data, headers=self._headers(), timeout=10)
        r.raise_for_status()
        return r.json()

    # AUTH
    def register(self, license_key: str, username: str, password: str, roblox_username: str = "") -> dict:
        res = self._post("/auth/register", {"license_key": license_key, "username": username, "password": password, "roblox_username": roblox_username})
        self.token = res["token"]
        self.user = res["user"]
        return res

    def login(self, username: str, password: str) -> dict:
        res = self._post("/auth/login", {"username": username, "password": password})
        self.token = res["token"]
        self.user = res["user"]
        return res

    def update_profile(self, **kwargs) -> dict:
        res = self._patch("/auth/profile", kwargs)
        self.user = res
        return res

    def get_me(self) -> dict:
        self.user = self._get("/auth/me")
        return self.user

    # DATA
    def get_announcements(self) -> list:
        return self._get("/announcements/")

    def get_licenses(self) -> list:
        return self._get("/licenses/")

    # WEBSOCKET
    def on(self, event_type: str, callback: Callable):
        self._ws_callbacks.setdefault(event_type, []).append(callback)

    def connect_ws(self):
        if not self.token:
            return
        self._running = True
        self._ws_thread = threading.Thread(target=self._ws_loop, daemon=True)
        self._ws_thread.start()

    def disconnect_ws(self):
        self._running = False
        if self._ws:
            try:
                self._ws.close()
            except Exception:
                pass

    def _ws_loop(self):
        import websocket as ws_lib
        ws_url = self.base_url.replace("http://", "ws://").replace("https://", "wss://")
        url = f"{ws_url}/ws/{self.token}"

        def on_message(ws, message):
            try:
                data = json.loads(message)
                t = data.get("type", "")
                for cb in self._ws_callbacks.get(t, []):
                    cb(data)
                for cb in self._ws_callbacks.get("*", []):
                    cb(data)
            except Exception:
                pass

        def on_error(ws, error):
            for cb in self._ws_callbacks.get("error", []):
                cb({"type": "error", "error": str(error)})

        def on_close(ws, *args):
            if self._running:
                import time; time.sleep(3)
                self._ws_loop()

        def on_open(ws):
            self._ws = ws
            for cb in self._ws_callbacks.get("connected", []):
                cb({"type": "connected"})

        wsa = ws_lib.WebSocketApp(url, on_message=on_message, on_error=on_error, on_close=on_close, on_open=on_open)
        wsa.run_forever(ping_interval=30)

    def send_ws(self, data: dict):
        if self._ws:
            try:
                self._ws.send(json.dumps(data))
            except Exception:
                pass

    def send_chat(self, content: str):
        self.send_ws({"type": "chat", "content": content})
