"""
VLK Launcher — Voice Engine
Real voice chat: PyAudio capture → Opus compression → WebSocket relay.
Fixed for Windows (WASAPI) and macOS (CoreAudio) compatibility.
"""
import io
import json
import base64
import threading
import time
import struct
from typing import Callable, Optional

try:
    import pyaudio
    PYAUDIO_OK = True
except ImportError:
    PYAUDIO_OK = False

try:
    import opuslib
    OPUS_OK = True
except ImportError:
    OPUS_OK = False

SAMPLE_RATE     = 48000
CHANNELS        = 1
CHUNK_MS        = 20                             # 20ms frames (Opus standard)
CHUNK_FRAMES    = int(SAMPLE_RATE * CHUNK_MS / 1000)  # 960
FORMAT_PA       = 8   # pyaudio.paInt16 == 8
SILENCE_THRESHOLD = 400                          # RMS threshold for VAD


def _rms(data: bytes) -> float:
    count = len(data) // 2
    if count == 0:
        return 0.0
    shorts = struct.unpack(f"<{count}h", data)
    return (sum(s * s for s in shorts) / count) ** 0.5


def _find_input_device(pa) -> int | None:
    """Return the best available input device index, preferring the default."""
    try:
        idx = pa.get_default_input_device_info()["index"]
        return idx
    except Exception:
        pass
    # Fallback: scan for any input device
    for i in range(pa.get_device_count()):
        info = pa.get_device_info_by_index(i)
        if info.get("maxInputChannels", 0) > 0:
            return i
    return None


def _find_output_device(pa) -> int | None:
    """Return the best available output device index."""
    try:
        idx = pa.get_default_output_device_info()["index"]
        return idx
    except Exception:
        pass
    for i in range(pa.get_device_count()):
        info = pa.get_device_info_by_index(i)
        if info.get("maxOutputChannels", 0) > 0:
            return i
    return None


class VoiceEngine:
    """
    Captures mic → encodes with Opus → sends via send_fn(dict).
    Receives encoded audio → decodes → plays out.
    """

    def __init__(self, send_fn: Callable[[dict], None], username: str):
        self._send = send_fn
        self._username = username
        self._running = False
        self._muted = False
        self._deafened = False
        self._speaking = False

        self.on_speaking_change: Optional[Callable[[bool], None]] = None
        self.on_peer_speaking: Optional[Callable[[str, bool], None]] = None

        self._pa = None
        self._in_stream = None
        self._out_stream = None
        self._enc = None
        self._dec = None

        self._playback_buffers: dict[str, list[bytes]] = {}
        self._playback_lock = threading.Lock()

        self._capture_thread: Optional[threading.Thread] = None
        self._playback_thread: Optional[threading.Thread] = None

    # ── Public API ────────────────────────────────────────────────────────────

    def start(self) -> tuple[bool, str]:
        """Start capture + playback. Returns (success, error_msg)."""
        if not PYAUDIO_OK:
            return False, (
                "pyaudio non installé.\n"
                "Windows : pip install pyaudio\n"
                "macOS   : brew install portaudio && pip install pyaudio"
            )
        if not OPUS_OK:
            return False, "opuslib non installé. Lancez : pip install opuslib"

        try:
            self._pa = pyaudio.PyAudio()

            in_dev = _find_input_device(self._pa)
            out_dev = _find_output_device(self._pa)

            if in_dev is None:
                return False, "Aucun microphone détecté."
            if out_dev is None:
                return False, "Aucun périphérique audio de sortie détecté."

            self._enc = opuslib.Encoder(SAMPLE_RATE, CHANNELS, opuslib.APPLICATION_VOIP)
            self._dec = opuslib.Decoder(SAMPLE_RATE, CHANNELS)

            # Open input stream – use explicit device index to avoid WASAPI issues
            self._in_stream = self._pa.open(
                format=FORMAT_PA,
                channels=CHANNELS,
                rate=SAMPLE_RATE,
                input=True,
                input_device_index=in_dev,
                frames_per_buffer=CHUNK_FRAMES,
            )
            # Open output stream
            self._out_stream = self._pa.open(
                format=FORMAT_PA,
                channels=CHANNELS,
                rate=SAMPLE_RATE,
                output=True,
                output_device_index=out_dev,
                frames_per_buffer=CHUNK_FRAMES,
            )

            self._running = True
            self._capture_thread = threading.Thread(
                target=self._capture_loop, daemon=True, name="vlk-capture"
            )
            self._playback_thread = threading.Thread(
                target=self._playback_loop, daemon=True, name="vlk-playback"
            )
            self._capture_thread.start()
            self._playback_thread.start()
            return True, ""

        except OSError as e:
            self.stop()
            # Common on Windows if no mic permission
            if "Invalid number of channels" in str(e) or "Invalid sample rate" in str(e):
                return False, (
                    "Paramètres audio non supportés par votre appareil.\n"
                    "Vérifiez que le micro est autorisé dans les paramètres système."
                )
            return False, f"Erreur audio : {e}"
        except Exception as e:
            self.stop()
            return False, f"Erreur inattendue : {e}"

    def stop(self):
        self._running = False
        for stream in (self._in_stream, self._out_stream):
            if stream:
                try:
                    stream.stop_stream()
                    stream.close()
                except Exception:
                    pass
        if self._pa:
            try:
                self._pa.terminate()
            except Exception:
                pass
        self._in_stream = self._out_stream = self._pa = None

    def set_muted(self, muted: bool):
        self._muted = muted

    def set_deafened(self, deafened: bool):
        self._deafened = deafened

    def is_muted(self) -> bool:
        return self._muted

    def is_deafened(self) -> bool:
        return self._deafened

    def is_running(self) -> bool:
        return self._running

    def receive_audio(self, from_user: str, encoded_b64: str):
        """Called when an audio packet arrives from the server."""
        if self._deafened or not self._running or not self._dec:
            return
        try:
            encoded = base64.b64decode(encoded_b64)
            pcm = self._dec.decode(encoded, CHUNK_FRAMES)
            with self._playback_lock:
                if from_user not in self._playback_buffers:
                    self._playback_buffers[from_user] = []
                self._playback_buffers[from_user].append(pcm)
            if self.on_peer_speaking:
                self.on_peer_speaking(from_user, True)
        except Exception:
            pass

    # ── Capture loop ──────────────────────────────────────────────────────────

    def _capture_loop(self):
        silence_frames = 0
        while self._running:
            try:
                raw = self._in_stream.read(CHUNK_FRAMES, exception_on_overflow=False)
            except OSError:
                # Stream interrupted (e.g. device unplugged) — wait and retry
                time.sleep(0.05)
                continue

            if self._muted:
                if self._speaking:
                    self._speaking = False
                    if self.on_speaking_change:
                        self.on_speaking_change(False)
                continue

            rms = _rms(raw)
            speaking = rms > SILENCE_THRESHOLD

            if speaking:
                silence_frames = 0
                if not self._speaking:
                    self._speaking = True
                    if self.on_speaking_change:
                        self.on_speaking_change(True)
                try:
                    encoded = self._enc.encode(raw, CHUNK_FRAMES)
                    b64 = base64.b64encode(encoded).decode()
                    self._send({
                        "type": "voice_audio",
                        "from": self._username,
                        "data": b64,
                    })
                except Exception:
                    pass
            else:
                silence_frames += 1
                if silence_frames >= 5 and self._speaking:
                    self._speaking = False
                    if self.on_speaking_change:
                        self.on_speaking_change(False)

    # ── Playback loop ─────────────────────────────────────────────────────────

    def _playback_loop(self):
        while self._running:
            played_any = False
            with self._playback_lock:
                users = list(self._playback_buffers.keys())

            for user in users:
                with self._playback_lock:
                    buf = self._playback_buffers.get(user, [])
                    if buf:
                        chunk = buf.pop(0)
                        if not buf:
                            self._playback_buffers.pop(user, None)
                            if self.on_peer_speaking:
                                self.on_peer_speaking(user, False)
                    else:
                        chunk = None

                if chunk and self._out_stream:
                    try:
                        self._out_stream.write(chunk)
                        played_any = True
                    except OSError:
                        pass

            if not played_any:
                time.sleep(0.005)
