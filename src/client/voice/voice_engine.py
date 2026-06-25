"""
VLK Launcher — Voice Engine
Real voice chat: PyAudio capture → Opus compression → WebSocket relay.
Server echoes audio to all participants in the same voice room.
No external service required — fully self-hosted over the existing WS server.
"""
import io
import json
import base64
import threading
import time
from typing import Callable, Optional

try:
    import pyaudio
    PYAUDIO_OK = True
except ImportError:
    PYAUDIO_OK = False

# Lazy import opuslib to avoid crash on startup if library is missing
# Note: opuslib has a syntax warning about "is not" vs "!=" - this is a third-party library issue and can be ignored
OPUS_OK = False
def _get_opuslib():
    global OPUS_OK
    if not OPUS_OK:
        try:
            import opuslib
            OPUS_OK = True
            return opuslib
        except ImportError:
            return None
    else:
        import opuslib
        return opuslib

SAMPLE_RATE   = 48000
CHANNELS      = 1
CHUNK_MS      = 20                        # 20ms frames (Opus standard)
CHUNK_FRAMES  = int(SAMPLE_RATE * CHUNK_MS / 1000)  # 960
FORMAT_PA     = 8   # pyaudio.paInt16
SILENCE_THRESHOLD = 500                   # RMS threshold for VAD


class VoiceEngine:
    """
    Captures mic → encodes with Opus → sends via send_fn(bytes).
    Receives encoded audio → decodes → plays out.
    """

    def __init__(self, send_fn: Callable[[dict], None], username: str):
        self._send = send_fn
        self._username = username
        self._running = False
        self._muted = False
        self._deafened = False
        self._speaking = False

        # Callbacks - disabled to prevent threading issues
        self.on_speaking_change: Optional[Callable[[bool], None]] = None
        self.on_peer_speaking: Optional[Callable[[str, bool], None]] = None

        # PyAudio
        self._pa = None
        self._in_stream = None
        self._out_stream = None

        # Opus
        self._enc = None
        self._dec = None

        # Playback buffer per user
        self._playback_buffers: dict[str, list[bytes]] = {}
        self._playback_lock = threading.Lock()

        self._capture_thread: Optional[threading.Thread] = None
        self._playback_thread: Optional[threading.Thread] = None

    # ── Public API ────────────────────────────────────────────────────────────

    def start(self) -> tuple[bool, str]:
        """Start capture + playback. Returns (success, error_msg)."""
        if not PYAUDIO_OK:
            return False, "pyaudio not installed. Run: pip install pyaudio"
        
        opuslib = _get_opuslib()
        if not opuslib:
            return False, "opuslib not installed. Run: pip install opuslib"

        try:
            # Suppress ALSA/Jack warnings by redirecting stderr and setting environment variables
            import sys
            import io
            import os
            
            # Set environment variables to suppress ALSA/Jack warnings
            os.environ['ALSA_VERBOSE'] = '0'
            os.environ['JACK_NO_START_SERVER'] = '1'
            
            old_stderr = sys.stderr
            old_stdout = sys.stdout
            sys.stderr = io.StringIO()
            sys.stdout = io.StringIO()
            
            try:
                self._pa = pyaudio.PyAudio()
                self._enc = opuslib.Encoder(SAMPLE_RATE, CHANNELS, opuslib.APPLICATION_VOIP)
                self._dec = opuslib.Decoder(SAMPLE_RATE, CHANNELS)

                # Try to get default devices, with fallbacks
                try:
                    input_device = None
                    output_device = None
                    
                    # Try to find working devices
                    for i in range(self._pa.get_device_count()):
                        info = self._pa.get_device_info_by_index(i)
                        if info['maxInputChannels'] > 0 and input_device is None:
                            input_device = i
                        if info['maxOutputChannels'] > 0 and output_device is None:
                            output_device = i
                    
                    # Open input stream with device selection
                    self._in_stream = self._pa.open(
                        format=FORMAT_PA,
                        channels=CHANNELS,
                        rate=SAMPLE_RATE,
                        input=True,
                        input_device_index=input_device,
                        frames_per_buffer=CHUNK_FRAMES,
                    )
                    
                    # Open output stream with device selection
                    self._out_stream = self._pa.open(
                        format=FORMAT_PA,
                        channels=CHANNELS,
                        rate=SAMPLE_RATE,
                        output=True,
                        output_device_index=output_device,
                        frames_per_buffer=CHUNK_FRAMES,
                    )
                except Exception as device_error:
                    # Fallback to default devices if specific device selection fails
                    self._in_stream = self._pa.open(
                        format=FORMAT_PA,
                        channels=CHANNELS,
                        rate=SAMPLE_RATE,
                        input=True,
                        frames_per_buffer=CHUNK_FRAMES,
                    )
                    self._out_stream = self._pa.open(
                        format=FORMAT_PA,
                        channels=CHANNELS,
                        rate=SAMPLE_RATE,
                        output=True,
                        frames_per_buffer=CHUNK_FRAMES,
                    )
                
                self._running = True
                self._capture_thread = threading.Thread(target=self._capture_loop, daemon=True, name="VoiceCaptureThread")
                self._playback_thread = threading.Thread(target=self._playback_loop, daemon=True, name="VoicePlaybackThread")
                self._capture_thread.start()
                self._playback_thread.start()
                return True, ""
            finally:
                # Restore stderr and stdout
                sys.stderr = old_stderr
                sys.stdout = old_stdout
                
        except Exception as e:
            self.stop()
            return False, str(e)

    def stop(self):
        self._running = False
        # Wait for threads to finish
        if self._capture_thread and self._capture_thread.is_alive():
            self._capture_thread.join(timeout=1.0)
        if self._playback_thread and self._playback_thread.is_alive():
            self._playback_thread.join(timeout=1.0)
        if self._in_stream:
            try: self._in_stream.stop_stream(); self._in_stream.close()
            except: pass
        if self._out_stream:
            try: self._out_stream.stop_stream(); self._out_stream.close()
            except: pass
        if self._pa:
            try: self._pa.terminate()
            except: pass
        self._in_stream = self._out_stream = self._pa = None
        self._capture_thread = self._playback_thread = None

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
        """Called when audio packet arrives from server."""
        if self._deafened or not self._running:
            return
        try:
            encoded = base64.b64decode(encoded_b64)
            pcm = self._dec.decode(encoded, CHUNK_FRAMES)
            with self._playback_lock:
                if from_user not in self._playback_buffers:
                    self._playback_buffers[from_user] = []
                self._playback_buffers[from_user].append(pcm)
            # Callbacks disabled to prevent threading issues
            # if self.on_peer_speaking:
            #     self.on_peer_speaking(from_user, True)
        except Exception:
            pass

    # ── Internal loops ────────────────────────────────────────────────────────

    def _capture_loop(self):
        silence_frames = 0
        while self._running:
            try:
                raw = self._in_stream.read(CHUNK_FRAMES, exception_on_overflow=False)
                if self._muted:
                    if self._speaking:
                        self._speaking = False
                        # Callbacks disabled to prevent threading issues
                        # if self.on_speaking_change:
                        #     self.on_speaking_change(False)
                    continue

                # VAD — simple RMS
                rms = _rms(raw)
                speaking = rms > SILENCE_THRESHOLD

                if speaking:
                    silence_frames = 0
                    if not self._speaking:
                        self._speaking = True
                        # Callbacks disabled to prevent threading issues
                        # if self.on_speaking_change:
                        #     self.on_speaking_change(True)
                    # Encode + send
                    encoded = self._enc.encode(raw, CHUNK_FRAMES)
                    b64 = base64.b64encode(encoded).decode()
                    self._send({
                        "type": "voice_audio",
                        "from": self._username,
                        "data": b64,
                    })
                else:
                    silence_frames += 1
                    if silence_frames >= 5 and self._speaking:
                        self._speaking = False
                        # Callbacks disabled to prevent threading issues
                        # if self.on_speaking_change:
                        #     self.on_speaking_change(False)
            except Exception:
                time.sleep(0.01)
            # Small sleep to prevent CPU hogging
            time.sleep(0.001)

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
                            # Callbacks disabled to prevent threading issues
                            # if self.on_peer_speaking:
                            #     self.on_peer_speaking(user, False)
                    else:
                        chunk = None
                if chunk and self._out_stream:
                    try:
                        self._out_stream.write(chunk)
                        played_any = True
                    except Exception:
                        pass
            if not played_any:
                time.sleep(0.005)


def _rms(data: bytes) -> float:
    import struct
    count = len(data) // 2
    if count == 0:
        return 0.0
    shorts = struct.unpack(f"<{count}h", data)
    return (sum(s * s for s in shorts) / count) ** 0.5
