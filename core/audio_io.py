import os
import sounddevice as sd
import numpy as np
import whisper
import queue
import time
from loguru import logger
from ui.state import state

_whisper_model = None

def get_model(model_size="base"):
    global _whisper_model
    if _whisper_model is None:
        logger.info(f"Loading Whisper model ({model_size}) into shared memory...")
        _whisper_model = whisper.load_model(model_size)
    return _whisper_model

class AudioInterface:
    def __init__(self, model_size="base", device_index=None, silence_threshold=500, silence_duration=1.5):
        self.model_size = model_size
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

    def extract_wave(self, chunk):
        if len(chunk) == 0:
            return [0]*64
        scaled = chunk.flatten() * 32768
        bins = np.array_split(scaled, 64)
        return [int(np.linalg.norm(b) / (len(b) + 1)) for b in bins]

    def listen_and_transcribe(self, on_speech_start=None):
        """
        Listens to the microphone. 
        Records audio until silence is detected for `silence_duration` seconds.
        Then transcribes the recorded audio.
        """
        model = get_model(self.model_size)
        q = queue.Queue()
        state["status"] = "listening"
        state["audio_source"] = "mic"
        state["audio_level"] = 0.0
        state["waveform"] = [0]*64
        
        def audio_callback(indata, frames, time, status):
            if status:
                logger.warning(f"Audio status: {status}")
            q.put(indata.copy())

        logger.info("Listening...")
        
        try:
            stream = sd.InputStream(
                samplerate=self.samplerate,
                channels=self.channels,
                device=self.device_index,
                callback=audio_callback,
                dtype='float32'
            )
        except Exception as e:
            logger.error(f"Microphone stream init failed: {e}")
            state["status"] = "idle"
            state["audio_level"] = 0.0
            state["waveform"] = [0] * 64
            state["audio_source"] = "mic"
            return ""
        
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
                state["audio_level"] = float(rms)
                state["waveform"] = self.extract_wave(chunk)
                state["audio_source"] = "mic"
                
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
                    state["audio_level"] = float(rms)
                    audio_data.append(chunk)
                    if silence_start_time is None:
                        silence_start_time = time.time()
                    
                    # If silence duration exceeds threshold, stop recording
                    if time.time() - silence_start_time > self.silence_duration:
                        break

        # If they spoke for less than 0.5 seconds, probably just noise
        if not audio_data or started_talking_time is None or (time.time() - started_talking_time < 0.5):
            state["status"] = "idle"
            state["audio_level"] = 0.0
            state["waveform"] = [0]*64
            state["audio_source"] = "mic"
            return ""

        # Concatenate chunks
        recording = np.concatenate(audio_data, axis=0).flatten().astype(np.float32)
        max_amp = float(np.max(np.abs(recording))) if recording.size else 0.0
        if max_amp > 0:
            recording = recording / max_amp

        logger.info("Processing speech to text...")
        try:
            result = model.transcribe(recording, fp16=False)
            text = result["text"].strip()
            logger.info(f"User Transcribed: {text}")
            state["status"] = "idle"
            state["audio_level"] = 0.0
            state["waveform"] = [0] * 64
            state["audio_source"] = "mic"
            return text
        except Exception as e:
            logger.error(f"Whisper transcription error: {e}")
            state["status"] = "idle"
            state["audio_level"] = 0.0
            state["waveform"] = [0]*64
            state["audio_source"] = "mic"
            return ""
        finally:
            state["audio_level"] = 0.0
            state["waveform"] = [0]*64
            state["audio_source"] = "mic"
