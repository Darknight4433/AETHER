import os
from elevenlabs import Voice, VoiceSettings
from elevenlabs.client import ElevenLabs
import pygame
from loguru import logger
import tempfile
import io

class SpeechEngine:
    def __init__(self, api_key, voice_id="21m00Tcm4TlvDq8ikWAM"): # Rachel by default
        self.api_key = api_key
        self.voice_id = voice_id
        
        if not api_key or api_key == "your_elevenlabs_api_key_here":
            logger.warning("ElevenLabs API key not set or invalid! TTS will not work.")
            self.client = None
        else:
            self.client = ElevenLabs(api_key=api_key)
            
        # Initialize pygame mixer for audio playback
        pygame.mixer.init()
        self.stop_flag = False

    def speak(self, text):
        """Generates speech via ElevenLabs and plays it locally (blocking)."""
        if not self.client:
            logger.error("Cannot speak: No ElevenLabs client.")
            return

        logger.info(f"Generating voice...")
        try:
            # Generate the audio stream
            audio_stream = self.client.generate(
                text=text,
                voice=Voice(
                    voice_id=self.voice_id,
                    settings=VoiceSettings(stability=0.71, similarity_boost=0.5, style=0.0, use_speaker_boost=True)
                ),
                model="eleven_multilingual_v2" # or eleven_turbo_v2
            )
            
            # Read generator into bytes
            audio_bytes = b"".join(list(audio_stream))
            
            # We need to save to a temp file because pygame mixer needs a file/buffer
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_audio:
                temp_audio.write(audio_bytes)
                temp_path = temp_audio.name
                
            # Play the audio
            pygame.mixer.music.load(temp_path)
            pygame.mixer.music.play()
            
            # Wait for playback to finish
            while pygame.mixer.music.get_busy():
                if self.stop_flag:
                    pygame.mixer.music.stop()
                    logger.info("🔇 Interrupted speaking.")
                    break
                pygame.time.Clock().tick(10)
                
            # Cleanup
            pygame.mixer.music.unload()
            try:
                os.remove(temp_path)
            except Exception:
                pass
                
        except Exception as e:
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
