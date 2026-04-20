import os
from elevenlabs import Voice, VoiceSettings
from elevenlabs.client import ElevenLabs
import pygame
from loguru import logger
import tempfile
import io
from ui.state import state

class SpeechEngine:
    def __init__(self, api_key, voice_id="21m00Tcm4TlvDq8ikWAM"): # Rachel by default
        self.api_keys = [k.strip() for k in str(api_key).split(",")] if api_key and api_key != "your_elevenlabs_api_key_here" else []
        self.voice_id = voice_id
        
        self.current_key_idx = 0
        if not self.api_keys:
            logger.warning("ElevenLabs API key not set or invalid! TTS will not work.")
            self.client = None
        else:
            self._init_client()
            
        # Initialize pygame mixer for audio playback
        pygame.mixer.init()
        self.stop_flag = False

    def _init_client(self):
        if self.current_key_idx < len(self.api_keys):
            logger.info(f"Binding ElevenLabs Node [Key {self.current_key_idx + 1}/{len(self.api_keys)}]")
            self.client = ElevenLabs(api_key=self.api_keys[self.current_key_idx])

    def speak(self, text):
        """Generates speech via ElevenLabs and plays it locally (blocking)."""
        if not self.client:
            logger.error("Cannot speak: No ElevenLabs client.")
            state["status"] = "idle"
            state["audio_level"] = 0.0
            state["audio_source"] = "mic"
            return

        state["status"] = "speaking"
        state["audio_source"] = "tts"
        state["audio_level"] = 0.0
        state["waveform"] = [0]*64
        logger.info(f"Generating voice...")
        try:
            # Generate the audio stream
            audio_stream = self.client.text_to_speech.convert(
                text=text,
                voice_id=self.voice_id,
                model_id="eleven_multilingual_v2",
                output_format="pcm_16000_16",
                voice_settings=VoiceSettings(
                    stability=0.71, 
                    similarity_boost=0.5, 
                    style=0.0, 
                    use_speaker_boost=True
                )
            )
            
            # Read generator into bytes
            audio_bytes = b"".join(audio_stream)
            
            import wave
            import numpy as np

            # We need to save to a temp file because pygame mixer needs a file/buffer
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
                temp_path = temp_audio.name
                
            with wave.open(temp_path, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(16000)
                wav_file.writeframes(audio_bytes)
                
            # Play the audio
            pygame.mixer.music.load(temp_path)
            pygame.mixer.music.play()
            
            samples = np.frombuffer(audio_bytes, dtype=np.int16)
            sample_rate = 16000
            
            # Streaming energy feedback loop
            chunk_size = 1024
            while pygame.mixer.music.get_busy():
                if self.stop_flag:
                    pygame.mixer.music.stop()
                    logger.info("🔇 Interrupted speaking.")
                    break
                
                # Approximate current sample position based on time
                pos_ms = pygame.mixer.music.get_pos()
                if pos_ms >= 0:
                    current_sample_idx = int((pos_ms / 1000.0) * sample_rate)
                    chunk = samples[current_sample_idx : current_sample_idx + chunk_size]
                    
                    if len(chunk) > 0:
                        # Real-time energy calculation for orb reactivity
                        energy = np.sqrt(np.mean(chunk.astype(np.float32)**2))
                        state["audio_level"] = float(energy) / 1000.0 # Normalized
                        
                        # Update waveform ring visualization
                        bins = np.array_split(chunk, 64)
                        state["waveform"] = [int(np.linalg.norm(b)/(len(b)+0.1)) for b in bins]

                pygame.time.Clock().tick(60) # High-frequency refresh for visuals
                
            # Reset status to idle after speaking
            state["status"] = "idle"
            state["audio_level"] = 0.0
            state["waveform"] = [0]*64
            state["audio_source"] = "mic"
            
            # Cleanup
            pygame.mixer.music.unload()
            try:
                os.remove(temp_path)
            except Exception:
                pass
                
        except Exception as e:
            error_msg = str(e).lower()
            if "quota" in error_msg or "unauthorized" in error_msg or "401" in error_msg or "429" in error_msg:
                logger.warning("ElevenLabs Quota Reached! Activating automatic key rotation...")
                self.current_key_idx += 1
                if self.current_key_idx < len(self.api_keys):
                    self._init_client()
                    return self.speak(text)  # Recursive retry with fresh Node
                else:
                    logger.error("FATAL: All mapped ElevenLabs API keys have exhausted quotas.")
            else:
                logger.error(f"ElevenLabs error: {e}")

    def speak_async(self, text):
        """Spawns a background thread to generate and play audio without blocking."""
        self.stop_flag = False
        import threading
        thread = threading.Thread(target=self.speak, args=(text,))
        thread.daemon = True
        thread.start()

    def stop_speaking(self):
        """Immediately sets flag to halt current speech playback."""
        self.stop_flag = True
