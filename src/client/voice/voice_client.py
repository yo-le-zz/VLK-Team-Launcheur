"""
VLK Launcher — Voice Integration Layer
Supports: LiveKit (preferred), Mumble (fallback), WebRTC stub
Does NOT implement raw voice capture/mixing — uses external services.
"""
import os
import subprocess
import platform
import webbrowser
from typing import Optional


class VoiceIntegration:
    """Abstract voice service integration.
    
    Configure via environment variables:
      VOICE_SERVICE=livekit|mumble|webrtc
      LIVEKIT_URL=wss://your-livekit-server
      LIVEKIT_ROOM=vlk-main
    """

    def __init__(self):
        self.service = os.environ.get("VOICE_SERVICE", "livekit")
        self.livekit_url = os.environ.get("LIVEKIT_URL", "")
        self.livekit_room = os.environ.get("LIVEKIT_ROOM", "vlk-main")
        self.mumble_host = os.environ.get("MUMBLE_HOST", "")
        self.mumble_port = int(os.environ.get("MUMBLE_PORT", "64738"))
        self._connected = False

    def connect(self, username: str, token: Optional[str] = None) -> bool:
        """Connect to voice service. Returns True on success."""
        if self.service == "livekit":
            return self._connect_livekit(username, token)
        elif self.service == "mumble":
            return self._connect_mumble(username)
        elif self.service == "webrtc":
            return self._connect_webrtc(username)
        return False

    def disconnect(self):
        self._connected = False

    def is_connected(self) -> bool:
        return self._connected

    # ── LiveKit ───────────────────────────────────────────────────────────────
    def _connect_livekit(self, username: str, token: str = None) -> bool:
        """
        Open LiveKit web client or launch LiveKit Meet.
        In production: generate a token server-side via /voice/token endpoint.
        """
        if not self.livekit_url:
            return False
        # Fallback: open LiveKit Meet web UI in browser
        meet_url = f"{self.livekit_url.replace('wss://', 'https://').replace('ws://', 'http://')}/rooms/{self.livekit_room}?username={username}"
        webbrowser.open(meet_url)
        self._connected = True
        return True

    # ── Mumble ────────────────────────────────────────────────────────────────
    def _connect_mumble(self, username: str) -> bool:
        """Launch Mumble client with VLK server preset."""
        if not self.mumble_host:
            return False
        url = f"mumble://{username}@{self.mumble_host}:{self.mumble_port}/VLK"
        try:
            if platform.system() == "Windows":
                subprocess.Popen(["start", url], shell=True)
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", url])
            else:
                subprocess.Popen(["xdg-open", url])
            self._connected = True
            return True
        except Exception:
            return False

    # ── WebRTC stub ───────────────────────────────────────────────────────────
    def _connect_webrtc(self, username: str) -> bool:
        """
        WebRTC integration stub.
        Implement via embedded WebEngineView + Jitsi Meet or similar.
        """
        webrtc_url = os.environ.get("WEBRTC_URL", "")
        if webrtc_url:
            webbrowser.open(f"{webrtc_url}?username={username}&room=vlk-main")
            self._connected = True
            return True
        return False

    def get_service_name(self) -> str:
        return {"livekit": "LiveKit", "mumble": "Mumble", "webrtc": "WebRTC"}.get(self.service, "Voice")


# Singleton
_voice = VoiceIntegration()

def get_voice_client() -> VoiceIntegration:
    return _voice
