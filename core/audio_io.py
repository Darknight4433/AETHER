import sounddevice as sd
import numpy as np
import whisper
import queue
import time
from loguru import logger
import tempfile
import soundfile as sf
import os

class AudioInterface:
    def __init__(self, model_size="base", device_index=None, silence_threshold=500, silence_duration=1.5):
        logger.info(f"Loading Whisper model ({model_size})...")
        self.model = whisper.load_model(model_size)
        self.device_index = device_index
        
        self.samplerate = 16000  # Whisper expects 16k Hz
        self.channels = 1
        
        self.silence_threshold = silence_threshold
        self.silence_duration = silence_duration
        
    def calculate_rms(self, audio_chunk):
        """Calculate Root Mean Square (energy) of the audio chunk."""
        # Check if the chunk is not completely empty
        if np.max(audio_chunk) == 0 and np.min(audio_chunk) == 0:
            return 0
            
        scaled_chunk = audio_chunk * 32768
        return np.sqrt(np.mean(scaled_chunk**2))

    def listen_and_transcribe(self, on_speech_start=None):
        """
        Listens to the microphone. 
        Records audio until silence is detected for `silence_duration` seconds.
        Then transcribes the recorded audio.
        """
        q = queue.Queue()
        
        def audio_callback(indata, frames, time, status):
            if status:
                logger.warning(f"Audio status: {status}")
            q.put(indata.copy())

        logger.info("Listening...")
        
        stream = sd.InputStream(
            samplerate=self.samplerate, 
            channels=self.channels,
            device=self.device_index,
            callback=audio_callback,
            dtype='float32'
        )
        
        audio_data = []
        is_speaking = False
        silence_start_time = None
        started_talking_time = None

        with stream:
            while True:
                try:
                    chunk = q.get(timeout=0.1)
                except queue.Empty:
                    continue
                    
                rms = self.calculate_rms(chunk)
                
                # If loudness is above threshold, someone is speaking
                if rms > self.silence_threshold:
                    if not is_speaking:
                        is_speaking = True
                        started_talking_time = time.time()
                        logger.debug(f"Voice detected (RMS: {rms:.1f})")
                        if on_speech_start:
                            on_speech_start()
                    silence_start_time = None
                    audio_data.append(chunk)
                elif is_speaking:
                    # Silence detected while speaking
                    audio_data.append(chunk)
                    if silence_start_time is None:
                        silence_start_time = time.time()
                    
                    # If silence duration exceeds threshold, stop recording
                    if time.time() - silence_start_time > self.silence_duration:
                        break

        # If they spoke for less than 0.5 seconds, probably just noise
        if not audio_data or (time.time() - started_talking_time < 0.5):
            return ""

        # Concatenate chunks
        recording = np.concatenate(audio_data, axis=0).flatten()
        
        # Save to temp file since Whisper expects a file path
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
            temp_path = temp_wav.name
            sf.write(temp_path, recording, self.samplerate)
        
        logger.info("Processing speech to text...")
        try:
            result = self.model.transcribe(temp_path, fp16=False)
            text = result["text"].strip()
            logger.info(f"User Transcribed: {text}")
            return text
        except Exception as e:
            logger.error(f"Whisper transcription error: {e}")
            return ""
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
