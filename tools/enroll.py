#!/usr/bin/env python3
"""
Voice Profile Enrollment Tool
Records your voice and creates a unique voiceprint for speaker identification.

Usage:
    python tools/enroll.py <name>
    
Example:
    python tools/enroll.py vaish
    
This will prompt you to record a 5-10 second sample.
"""

import sys
import os
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sounddevice as sd
import numpy as np
import soundfile as sf
from loguru import logger

from core.voice_id import embed_wav, save_profile


def record_audio(duration=10, sample_rate=16000, device=None):
    """
    Record audio from microphone.
    
    Args:
        duration: Recording duration in seconds
        sample_rate: Sample rate (Hz)
        device: Audio device index (None = default)
        
    Returns:
        numpy array of audio samples
    """
    print(f"\n🎙️  Recording for {duration} seconds...")
    print("Speak clearly and naturally. Try to use similar tone/speed as daily use.")
    print("Starting in 2 seconds...\n")
    time.sleep(2)
    
    try:
        # Record audio
        audio = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype=np.float32,
            device=device
        )
        
        # Show progress
        for i in range(duration):
            print(f"  Recording... {i+1}s", end="\r")
            time.sleep(1)
        
        sd.wait()
        print("\n✓ Recording complete\n")
        return audio
        
    except Exception as e:
        logger.error(f"Recording failed: {e}")
        return None


def enroll_user(name: str, audio_data: np.ndarray, output_path: str):
    """
    Enroll a user by creating and saving voice profile.
    
    Args:
        name: User name
        audio_data: Numpy array of audio samples
        output_path: Path to save temporary WAV file
    """
    # Save raw audio to temp WAV
    sample_rate = 16000
    sf.write(output_path, audio_data, sample_rate)
    logger.info(f"Saved audio to {output_path}")
    
    # Create embedding
    print("\n🧠 Creating voice embedding...")
    embedding = embed_wav(output_path)
    
    if embedding is None:
        logger.error("Failed to create embedding!")
        return False
    
    # Save profile
    if save_profile(name, embedding):
        print(f"\n✅ Voice profile created for '{name}'!")
        print(f"   Embedding dimension: {len(embedding)}")
        print(f"   Profile saved to: data/voice_profiles/{name}.npy")
        return True
    else:
        logger.error("Failed to save profile!")
        return False


def main():
    if len(sys.argv) < 2:
        print("Usage: python tools/enroll.py <name>")
        print("Example: python tools/enroll.py vaish")
        sys.exit(1)
    
    name = sys.argv[1].lower()
    
    # Validate name
    if not name.isalnum():
        print("❌ Name must be alphanumeric (no spaces or special chars)")
        sys.exit(1)
    
    print("\n" + "="*60)
    print(f"  AETHER VOICE ENROLLMENT — {name.upper()}")
    print("="*60)
    
    # Record audio
    audio_data = record_audio(duration=10)
    if audio_data is None:
        sys.exit(1)
    
    # Save temporarily and create profile
    temp_path = f"data/enroll_{name}_temp.wav"
    success = enroll_user(name, audio_data, temp_path)
    
    # Cleanup temp file
    try:
        if os.path.exists(temp_path):
            os.remove(temp_path)
    except:
        pass
    
    if success:
        print("\n" + "="*60)
        print(f"✅ {name.upper()} is now enrolled!")
        print("   You can now use Aether with voice authentication.")
        print("="*60 + "\n")
    else:
        print("\n❌ Enrollment failed. Please try again.\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
