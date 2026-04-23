import os
import tempfile
import threading
import wave

import numpy as np
import pygame
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs
from loguru import logger

from ui.state import state


class SpeechEngine:
    def __init__(self, api_key, voice_id="21m00Tcm4TlvDq8ikWAM"):
        self.api_keys = [
            k.strip() for k in str(api_key).split(",")
            if k.strip()
        ] if api_key and api_key != "your_elevenlabs_api_key_here" else []
        self.voice_id = voice_id
        self.current_key_idx = 0
        self.client = None
        self.stop_flag = False

        if not self.api_keys:
            logger.warning("ElevenLabs API key not set or invalid. TTS will not work.")
        else:
            self._init_client()

        self.audio_ready = self._init_audio()

    def _init_audio(self):
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            return True
        except Exception as e:
            logger.error(f"Audio output init failed: {e}")
            return False

    def _init_client(self):
        if self.current_key_idx < len(self.api_keys):
            logger.info(
                f"Binding ElevenLabs Node [Key {self.current_key_idx + 1}/{len(self.api_keys)}]"
            )
            self.client = ElevenLabs(api_key=self.api_keys[self.current_key_idx])

    def _reset_audio_state(self):
        state["status"] = "idle"
        state["audio_level"] = 0.0
        state["waveform"] = [0] * 64
        state["audio_source"] = "mic"

    def speak(self, text):
        """Generate speech via ElevenLabs and play it locally."""
        if not text:
            self._reset_audio_state()
            return

        if not self.client:
            logger.error("Cannot speak: No ElevenLabs client.")
            state["last_action"] = "TTS unavailable"
            self._reset_audio_state()
            return

        if not self.audio_ready and not self._init_audio():
            logger.error("Cannot speak: Audio output is unavailable.")
            state["last_action"] = "Audio output unavailable"
            self._reset_audio_state()
            return

        state["status"] = "speaking"
        state["audio_source"] = "tts"
        state["audio_level"] = 0.0
        state["waveform"] = [0] * 64
        logger.info("Generating voice...")
        temp_path = None

        try:
            audio_stream = self.client.text_to_speech.convert(
                text=text,
                voice_id=self.voice_id,
                model_id="eleven_turbo_v2_5",
                output_format="pcm_16000",
                voice_settings=VoiceSettings(
                    stability=0.5,
                    similarity_boost=0.75,
                    style=0.0,
                    use_speaker_boost=True,
                ),
            )

            audio_bytes = b"".join(audio_stream)
            if not audio_bytes:
                raise RuntimeError("ElevenLabs returned empty audio.")

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
                temp_path = temp_audio.name

            with wave.open(temp_path, "wb") as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(16000)
                wav_file.writeframes(audio_bytes)

            pygame.mixer.music.load(temp_path)
            pygame.mixer.music.play()

            samples = np.frombuffer(audio_bytes, dtype=np.int16)
            sample_rate = 16000
            chunk_size = 1024
            clock = pygame.time.Clock()

            while pygame.mixer.music.get_busy():
                if self.stop_flag:
                    pygame.mixer.music.stop()
                    logger.info("Speech interrupted.")
                    break

                pos_ms = pygame.mixer.music.get_pos()
                if pos_ms >= 0:
                    current_sample_idx = int((pos_ms / 1000.0) * sample_rate)
                    chunk = samples[current_sample_idx: current_sample_idx + chunk_size]
                    if len(chunk) > 0:
                        energy = np.sqrt(np.mean(chunk.astype(np.float32) ** 2))
                        state["audio_level"] = float(energy) / 1000.0
                        bins = np.array_split(chunk, 64)
                        state["waveform"] = [
                            int(np.linalg.norm(b) / (len(b) + 0.1)) for b in bins
                        ]

                clock.tick(60)

        except Exception as e:
            error_msg = str(e).lower()
            if any(token in error_msg for token in ["quota", "unauthorized", "401", "403", "429"]):
                logger.warning("ElevenLabs access issue detected. Trying the next API key.")
                self.current_key_idx += 1
                if self.current_key_idx < len(self.api_keys):
                    self._init_client()
                    return self.speak(text)
                logger.error("All configured ElevenLabs API keys are unavailable.")
            else:
                logger.error(f"ElevenLabs error: {e}")
        finally:
            self._reset_audio_state()
            try:
                if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
                    pygame.mixer.music.stop()
            except Exception:
                pass
            try:
                if pygame.mixer.get_init():
                    pygame.mixer.music.unload()
            except Exception:
                pass
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass

    def speak_async(self, text):
        """Spawn a background thread to generate and play audio."""
        self.stop_flag = False
        thread = threading.Thread(target=self.speak, args=(text,), daemon=True)
        thread.start()

    def stop_speaking(self):
        """Immediately halt current speech playback."""
        self.stop_flag = True
