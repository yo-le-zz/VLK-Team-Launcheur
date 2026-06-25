"""VLK Launcher — HTTP + WebSocket client core"""
import json
import threading
import requests
import os
import queue
from typing import Callable, Optional


class WSSignalDispatcher:
    """Dispatches WebSocket callbacks using a thread-safe queue."""

    def __init__(self, parent=None):
        self._callbacks: dict[str, list[Callable]] = {}
        self._queue: "queue.Queue[tuple[str, dict]]" = queue.Queue()
        self._timer_callback = None
        self._main_thread_id = threading.get_ident()

    def register_callback(self, event_type: str, callback: Callable):
        self._callbacks.setdefault(event_type, []).append(callback)

    def set_timer_callback(self, callback):
        """Set a QTimer.singleShot callback for thread safety."""
        self._timer_callback = callback

    def dispatch(self, event_type: str, data: dict):
        """Called from background thread, queues the event for main thread processing."""
        self._queue.put((event_type, data))
        # Schedule processing in main thread
        if self._timer_callback:
            self._timer_callback(self._process_queue)

    def _process_queue(self):
        """Process queued events in main thread."""
        try:
            while True:
                event_type, data = self._queue.get_nowait()
                self._handle_message(event_type, data)
        except queue.Empty:
            pass

    def _handle_message(self, event_type: str, data: dict):
        """Called in main thread."""
        for cb in self._callbacks.get(event_type, []):
            try:
                cb(data)
            except Exception as e:
                print(f"Error in callback for {event_type}: {e}")
        for cb in self._callbacks.get("*", []):
            try:
                cb(data)
            except Exception as e:
                print(f"Error in wildcard callback: {e}")


class VLKApiClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self.token: Optional[str] = None
        self.user: Optional[dict] = None

        # Server MASTER_PASSWORD, cached alongside the session so admin/superadmin
        # accounts don't have to re-enter it every relaunch.
        self.master_password: Optional[str] = None

        self._ws = None
        self._ws_thread: Optional[threading.Thread] = None
        self._ws_callbacks: dict[str, list[Callable]] = {}
        self._running = False

        self._cache_file = os.path.join(os.path.expanduser("~"), ".vlk_cache.json")

        # Derived from user password (salt). If present, cache is encrypted and needs unlocking.
        self._encryption_key: Optional[str] = None
        self._password_unlocked: bool = False
        self._last_login_password: Optional[str] = None

        self._main_thread_id = threading.get_ident()
        self._ws_dispatcher: Optional[WSSignalDispatcher] = None

        self._load_cached_session()

    def _load_cached_session(self):
        """Load cached token and user data from file."""
        try:
            if not os.path.exists(self._cache_file):
                return

            with open(self._cache_file, "r") as f:
                data = json.load(f)

            if data.get("encrypted"):
                self._encryption_key = data.get("encryption_key")
                self.token = None
                self.user = None
                self.master_password = None
                self._password_unlocked = False
            else:
                # Legacy / unencrypted format
                self.token = data.get("token")
                self.user = data.get("user")
                self.master_password = data.get("master_password")
                self._password_unlocked = True
        except Exception as e:
            print(f"Error loading cached session: {e}")

    def _save_cached_session(self, password: Optional[str] = None):
        """Save token, user data and (optionally) master password to file,
        with optional password-based encryption."""
        try:
            if not (self.token and self.user):
                return

            if password:
                # Use password-based encryption
                from src.client.core.crypto import CryptoManager

                crypto = CryptoManager(password)
                data = {
                    "encrypted": True,
                    "encryption_key": crypto.get_salt(),
                    "token": crypto.encrypt(self.token),
                    "user": crypto.encrypt(json.dumps(self.user)),
                    "master_password": crypto.encrypt(self.master_password or ""),
                    "unlocked": True,
                }
                self._password_unlocked = True
            else:
                # Unencrypted (not recommended)
                data = {
                    "token": self.token,
                    "user": self.user,
                    "master_password": self.master_password,
                }
                self._password_unlocked = True

            with open(self._cache_file, "w") as f:
                json.dump(data, f)
        except Exception:
            pass

    def _decrypt_cached_session(self, password: str) -> bool:
        """Decrypt cached session using provided password."""
        try:
            if not self._encryption_key:
                return False

            from src.client.core.crypto import CryptoManager

            crypto = CryptoManager.from_password_and_salt(password, self._encryption_key)
            with open(self._cache_file, "r") as f:
                data = json.load(f)

            token = crypto.decrypt(data.get("token", ""))
            user_json = crypto.decrypt(data.get("user", ""))
            user = json.loads(user_json) if user_json else None
            mpw = crypto.decrypt(data.get("master_password", "")) or None

            if token and user:
                self.token = token
                self.user = user
                self.master_password = mpw
                self._password_unlocked = True
                # Remember the account password so we can re-save the cache
                # later if a master password gets captured during this session.
                self._last_login_password = password
                return True
            return False
        except Exception:
            return False

    def _clear_cached_session(self):
        """Clear cached session data."""
        try:
            if os.path.exists(self._cache_file):
                os.remove(self._cache_file)
        except Exception:
            pass

        self.token = None
        self.user = None
        self.master_password = None
        self._encryption_key = None
        self._password_unlocked = False
        self._last_login_password = None

    def set_master_password(self, master_password: str, login_password: Optional[str] = None):
        """Cache the server MASTER_PASSWORD alongside the session so it
        doesn't need to be re-entered on every relaunch."""
        self.master_password = master_password
        pw = login_password or self._last_login_password
        self._save_cached_session(password=pw)

    def _headers(self) -> dict:
        h = {"Content-Type": "application/json"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def _post(self, path: str, data: dict) -> dict:
        r = requests.post(
            f"{self.base_url}{path}", json=data, headers=self._headers(), timeout=10
        )
        r.raise_for_status()
        return r.json()

    def _get(self, path: str) -> dict | list:
        r = requests.get(
            f"{self.base_url}{path}", headers=self._headers(), timeout=10
        )
        r.raise_for_status()
        return r.json()

    def _patch(self, path: str, data: dict) -> dict:
        r = requests.patch(
            f"{self.base_url}{path}", json=data, headers=self._headers(), timeout=10
        )
        r.raise_for_status()
        return r.json()

    # AUTH
    def register(
        self,
        license_key: str,
        username: str,
        password: str,
        roblox_username: str = "",
    ) -> dict:
        res = self._post(
            "/auth/register",
            {
                "license_key": license_key,
                "username": username,
                "password": password,
                "roblox_username": roblox_username,
            },
        )
        self.token = res["token"]
        self.user = res["user"]
        self._last_login_password = password
        self._save_cached_session(password=password)
        return res

    def login(self, username: str, password: str) -> dict:
        # Password-only login: unlock encrypted cache and verify via /auth/me
        if self._encryption_key and not username:
            if self._decrypt_cached_session(password):
                # Verify token is still valid
                user_data = self._get("/auth/me")
                self._password_unlocked = True
                self.user = user_data
                return {"token": self.token, "user": self.user}

        # Normal login flow (requires username)
        if not username:
            raise ValueError("Username required for login")

        res = self._post("/auth/login", {"username": username, "password": password})
        self.token = res["token"]
        self.user = res["user"]
        self._last_login_password = password
        self._save_cached_session(password=password)
        return res

    def logout(self):
        """Clear session and logout."""
        self.token = None
        self.user = None
        self._clear_cached_session()

    def update_profile(self, **kwargs) -> dict:
        res = self._patch("/auth/profile", kwargs)
        self.user = res
        return res

    def delete_account(self) -> dict:
        """Delete user account (frees license for reuse)."""
        r = requests.delete(
            f"{self.base_url}/auth/delete-account", headers=self._headers(), timeout=10
        )
        r.raise_for_status()
        return r.json()

    def get_me(self) -> dict:
        self.user = self._get("/auth/me")
        return self.user

    # DATA
    def get_announcements(self) -> list:
        return self._get("/announcements/")

    def get_licenses(self) -> list:
        return self._get("/licenses/")

    # WEBSOCKET
    def init_ws_dispatcher(self, parent=None):
        """Initialize the Qt signal dispatcher for thread-safe WebSocket callbacks."""
        self._ws_dispatcher = WSSignalDispatcher(parent)
        # Re-register existing callbacks
        for event_type, callbacks in self._ws_callbacks.items():
            for cb in callbacks:
                self._ws_dispatcher.register_callback(event_type, cb)

    def on(self, event_type: str, callback: Callable):
        self._ws_callbacks.setdefault(event_type, []).append(callback)
        if self._ws_dispatcher:
            self._ws_dispatcher.register_callback(event_type, callback)

    def connect_ws(self):
        if not self.token:
            return
        self._running = True
        self._ws_thread = threading.Thread(
            target=self._ws_loop, daemon=True, name="WebSocketThread"
        )
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

                if self._ws_dispatcher:
                    self._ws_dispatcher.dispatch(t, data)
                else:
                    # Fallback: direct call (not thread-safe)
                    for cb in self._ws_callbacks.get(t, []):
                        cb(data)
                    for cb in self._ws_callbacks.get("*", []):
                        cb(data)
            except Exception:
                pass

        def on_error(ws, error):
            if self._ws_dispatcher:
                self._ws_dispatcher.dispatch(
                    "error", {"type": "error", "error": str(error)}
                )
            else:
                for cb in self._ws_callbacks.get("error", []):
                    cb({"type": "error", "error": str(error)})

        def on_close(ws, *args):
            if self._running:
                import time

                time.sleep(3)
                self._ws_loop()

        def on_open(ws):
            self._ws = ws
            if self._ws_dispatcher:
                self._ws_dispatcher.dispatch("connected", {"type": "connected"})
            else:
                for cb in self._ws_callbacks.get("connected", []):
                    cb({"type": "connected"})

        wsa = ws_lib.WebSocketApp(
            url,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
            on_open=on_open,
        )
        wsa.run_forever(ping_interval=30)

    def send_ws(self, data: dict):
        if self._ws:
            try:
                self._ws.send(json.dumps(data))
            except Exception:
                pass

    def send_chat(self, content: str):
        self.send_ws({"type": "chat", "content": content})
