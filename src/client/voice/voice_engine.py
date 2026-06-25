"""
VLK Launcher — Voice Engine
Capture mic → encode Opus via ctypes → WebSocket relay.
Does NOT depend on opuslib Python package — loads libopus directly with ctypes
so PyInstaller bundles work on Windows and macOS without missing-DLL crashes.
"""
import base64
import ctypes
import ctypes.util
import os
import struct
import sys
import threading
import time
from typing import Callable, Optional

try:
    import pyaudio
    PYAUDIO_OK = True
except ImportError:
    PYAUDIO_OK = False

SAMPLE_RATE       = 48000
CHANNELS          = 1
CHUNK_MS          = 20
CHUNK_FRAMES      = int(SAMPLE_RATE * CHUNK_MS / 1000)   # 960 samples
FORMAT_PA         = 8    # paInt16
SILENCE_THRESHOLD = 400
OPUS_APPLICATION_VOIP = 2048
OPUS_OK_CODE          = 0


# ── Dynamic libopus loader ────────────────────────────────────────────────────

def _load_opus_lib():
    """
    Try to load libopus from several candidate locations in priority order:
    1. Next to the exe (bundled by PyInstaller via --add-binary)
    2. PyInstaller _MEIPASS temp dir
    3. System library paths
    """
    candidates = []

    if getattr(sys, "frozen", False):
        bundle_dir = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
        exe_dir    = os.path.dirname(sys.executable)
        if sys.platform == "win32":
            candidates += [
                os.path.join(exe_dir,    "opus.dll"),
                os.path.join(bundle_dir, "opus.dll"),
            ]
        elif sys.platform == "darwin":
            candidates += [
                os.path.join(exe_dir,    "libopus.dylib"),
                os.path.join(bundle_dir, "libopus.dylib"),
                os.path.join(exe_dir,    "libopus.0.dylib"),
                os.path.join(bundle_dir, "libopus.0.dylib"),
            ]
        else:
            candidates += [
                os.path.join(exe_dir,    "libopus.so.0"),
                os.path.join(bundle_dir, "libopus.so.0"),
            ]

    # Non-frozen / system fallbacks
    if sys.platform == "win32":
        candidates += ["opus.dll", "libopus-0.dll", "libopus.dll"]
    elif sys.platform == "darwin":
        candidates += [
            "/opt/homebrew/lib/libopus.dylib",    # Apple Silicon
            "/usr/local/lib/libopus.dylib",        # Intel homebrew
            "/usr/lib/libopus.dylib",
        ]
        found = ctypes.util.find_library("opus")
        if found:
            candidates.append(found)
    else:
        candidates += ["libopus.so.0", "libopus.so"]
        found = ctypes.util.find_library("opus")
        if found:
            candidates.append(found)

    for path in candidates:
        if not path:
            continue
        try:
            lib = ctypes.CDLL(path)
            lib.opus_get_version_string.restype = ctypes.c_char_p
            lib.opus_get_version_string()        # smoke test
            return lib
        except Exception:
            continue
    return None


_opus   = _load_opus_lib()
OPUS_OK = _opus is not None


# ── ctypes Opus encoder / decoder ─────────────────────────────────────────────

class _OpusEncoder:
    def __init__(self, lib, sample_rate: int, channels: int):
        lib.opus_encoder_get_size.restype  = ctypes.c_int
        lib.opus_encoder_get_size.argtypes = [ctypes.c_int]
        self._st  = ctypes.create_string_buffer(lib.opus_encoder_get_size(channels))
        self._lib = lib

        lib.opus_encoder_init.restype  = ctypes.c_int
        lib.opus_encoder_init.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int]
        rc = lib.opus_encoder_init(self._st, sample_rate, channels, OPUS_APPLICATION_VOIP)
        if rc != OPUS_OK_CODE:
            raise RuntimeError(f"opus_encoder_init: {rc}")

    def encode(self, pcm_bytes: bytes, frame_size: int) -> bytes:
        MAX = 1275
        out    = (ctypes.c_ubyte * MAX)()
        pcm_ct = (ctypes.c_int16 * (len(pcm_bytes) // 2)).from_buffer_copy(pcm_bytes)
        n = self._lib.opus_encode(self._st, pcm_ct, ctypes.c_int(frame_size), out, ctypes.c_int32(MAX))
        if n < 0:
            raise RuntimeError(f"opus_encode: {n}")
        return bytes(out[:n])


class _OpusDecoder:
    def __init__(self, lib, sample_rate: int, channels: int):
        lib.opus_decoder_get_size.restype  = ctypes.c_int
        lib.opus_decoder_get_size.argtypes = [ctypes.c_int]
        self._st       = ctypes.create_string_buffer(lib.opus_decoder_get_size(channels))
        self._lib      = lib
        self._channels = channels

        lib.opus_decoder_init.restype  = ctypes.c_int
        lib.opus_decoder_init.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
        rc = lib.opus_decoder_init(self._st, sample_rate, channels)
        if rc != OPUS_OK_CODE:
            raise RuntimeError(f"opus_decoder_init: {rc}")

    def decode(self, data: bytes, frame_size: int) -> bytes:
        pcm = (ctypes.c_int16 * (frame_size * self._channels))()
        n   = self._lib.opus_decode(
            self._st, data, ctypes.c_int32(len(data)),
            pcm, ctypes.c_int(frame_size), ctypes.c_int(0),
        )
        if n < 0:
            raise RuntimeError(f"opus_decode: {n}")
        return bytes(pcm[:n * self._channels])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _rms(data: bytes) -> float:
    count = len(data) // 2
    if not count:
        return 0.0
    shorts = struct.unpack(f"<{count}h", data)
    return (sum(s * s for s in shorts) / count) ** 0.5


def _find_input_device(pa):
    try:
        return pa.get_default_input_device_info()["index"]
    except Exception:
        pass
    for i in range(pa.get_device_count()):
        if pa.get_device_info_by_index(i).get("maxInputChannels", 0) > 0:
            return i
    return None


def _find_output_device(pa):
    try:
        return pa.get_default_output_device_info()["index"]
    except Exception:
        pass
    for i in range(pa.get_device_count()):
        if pa.get_device_info_by_index(i).get("maxOutputChannels", 0) > 0:
            return i
    return None


# ── VoiceEngine ───────────────────────────────────────────────────────────────

class VoiceEngine:
    def __init__(self, send_fn: Callable[[dict], None], username: str):
        self._send     = send_fn
        self._username = username
        self._running  = False
        self._muted    = False
        self._deafened = False
        self._speaking = False

        self.on_speaking_change: Optional[Callable[[bool], None]] = None
        self.on_peer_speaking:   Optional[Callable[[str, bool], None]] = None

        self._pa          = None
        self._in_stream   = None
        self._out_stream  = None
        self._enc: Optional[_OpusEncoder] = None
        self._dec: Optional[_OpusDecoder] = None

        self._playback_buffers: dict[str, list[bytes]] = {}
        self._playback_lock   = threading.Lock()
        self._capture_thread:  Optional[threading.Thread] = None
        self._playback_thread: Optional[threading.Thread] = None

    def start(self) -> tuple[bool, str]:
        if not PYAUDIO_OK:
            return False, (
                "PyAudio non installé.\n"
                "Windows : pip install pyaudio\n"
                "macOS   : brew install portaudio && pip install pyaudio"
            )
        if not OPUS_OK:
            return False, (
                "Librairie Opus introuvable.\n\n"
                "• Windows  → placez opus.dll dans le même dossier que VLKLauncher.exe\n"
                "  Téléchargez : https://opus-codec.org/downloads/  (opus-1.x.x-win.zip)\n\n"
                "• macOS    → brew install opus\n"
                "• Linux    → sudo apt install libopus0"
            )
        try:
            self._pa    = pyaudio.PyAudio()
            in_dev      = _find_input_device(self._pa)
            out_dev     = _find_output_device(self._pa)

            if in_dev is None:
                return False, "Aucun microphone détecté."
            if out_dev is None:
                return False, "Aucun périphérique de sortie audio détecté."

            self._enc = _OpusEncoder(_opus, SAMPLE_RATE, CHANNELS)
            self._dec = _OpusDecoder(_opus, SAMPLE_RATE, CHANNELS)

            self._in_stream = self._pa.open(
                format=FORMAT_PA, channels=CHANNELS, rate=SAMPLE_RATE,
                input=True, input_device_index=in_dev,
                frames_per_buffer=CHUNK_FRAMES,
            )
            self._out_stream = self._pa.open(
                format=FORMAT_PA, channels=CHANNELS, rate=SAMPLE_RATE,
                output=True, output_device_index=out_dev,
                frames_per_buffer=CHUNK_FRAMES,
            )
            self._running = True
            self._capture_thread  = threading.Thread(target=self._capture_loop,  daemon=True, name="vlk-capture")
            self._playback_thread = threading.Thread(target=self._playback_loop, daemon=True, name="vlk-playback")
            self._capture_thread.start()
            self._playback_thread.start()
            return True, ""
        except OSError as e:
            self.stop()
            return False, (
                f"Erreur audio : {e}\n"
                "Vérifiez que le micro est autorisé dans les paramètres de confidentialité système."
            )
        except Exception as e:
            self.stop()
            return False, f"Erreur inattendue : {e}"

    def stop(self):
        self._running = False
        for s in (self._in_stream, self._out_stream):
            if s:
                try: s.stop_stream(); s.close()
                except: pass
        if self._pa:
            try: self._pa.terminate()
            except: pass
        self._in_stream = self._out_stream = self._pa = None

    def set_muted(self, v: bool):    self._muted    = v
    def set_deafened(self, v: bool): self._deafened = v
    def is_muted(self)    -> bool:   return self._muted
    def is_deafened(self) -> bool:   return self._deafened
    def is_running(self)  -> bool:   return self._running

    def receive_audio(self, from_user: str, encoded_b64: str):
        if self._deafened or not self._running or not self._dec:
            return
        try:
            pcm = self._dec.decode(base64.b64decode(encoded_b64), CHUNK_FRAMES)
            with self._playback_lock:
                self._playback_buffers.setdefault(from_user, []).append(pcm)
            if self.on_peer_speaking:
                self.on_peer_speaking(from_user, True)
        except Exception:
            pass

    def _capture_loop(self):
        silence_frames = 0
        while self._running:
            try:
                raw = self._in_stream.read(CHUNK_FRAMES, exception_on_overflow=False)
            except OSError:
                time.sleep(0.05)
                continue

            if self._muted:
                if self._speaking:
                    self._speaking = False
                    if self.on_speaking_change: self.on_speaking_change(False)
                continue

            if _rms(raw) > SILENCE_THRESHOLD:
                silence_frames = 0
                if not self._speaking:
                    self._speaking = True
                    if self.on_speaking_change: self.on_speaking_change(True)
                try:
                    encoded = self._enc.encode(raw, CHUNK_FRAMES)
                    self._send({"type": "voice_audio", "from": self._username,
                                "data": base64.b64encode(encoded).decode()})
                except Exception:
                    pass
            else:
                silence_frames += 1
                if silence_frames >= 5 and self._speaking:
                    self._speaking = False
                    if self.on_speaking_change: self.on_speaking_change(False)

    def _playback_loop(self):
        while self._running:
            played = False
            with self._playback_lock:
                users = list(self._playback_buffers.keys())
            for user in users:
                with self._playback_lock:
                    buf   = self._playback_buffers.get(user, [])
                    chunk = buf.pop(0) if buf else None
                    if not buf:
                        self._playback_buffers.pop(user, None)
                        if chunk and self.on_peer_speaking:
                            self.on_peer_speaking(user, False)
                if chunk and self._out_stream:
                    try: self._out_stream.write(chunk); played = True
                    except OSError: pass
            if not played:
                time.sleep(0.005)
