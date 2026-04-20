"""
Voice identification module - lightweight speaker recognition via voiceprint similarity.
Uses resemblyzer for efficient on-device speaker embeddings.
"""

import os
import numpy as np
from loguru import logger

# Lazy initialization - only load when needed
encoder = None

def _get_encoder():
    """Get or initialize the voice encoder."""
    global encoder
    if encoder is None:
        try:
            from resemblyzer import VoiceEncoder
            encoder = VoiceEncoder()
            logger.success("Voice encoder loaded successfully")
        except Exception as e:
            logger.error(f"Failed to initialize voice encoder: {e}")
            encoder = None
    return encoder
    logger.error(f"Failed to initialize voice encoder: {e}")
    encoder = None

# Configuration
PROFILE_DIR = "data/voice_profiles"
THRESHOLD = 0.75  # Adjust 0.70-0.85 based on testing

os.makedirs(PROFILE_DIR, exist_ok=True)


def embed_wav(wav_path: str) -> np.ndarray:
    """
    Create a voiceprint embedding from a WAV file.
    
    Args:
        wav_path: Path to WAV file
        
    Returns:
        256-dim embedding vector
    """
    encoder = _get_encoder()
    if encoder is None:
        logger.error("Voice encoder not initialized")
        return None
    
    try:
        from resemblyzer import preprocess_wav
        wav = preprocess_wav(wav_path)
        embedding = encoder.embed_utterance(wav)
        return embedding
    except Exception as e:
        logger.error(f"Failed to embed audio {wav_path}: {e}")
        return None


def save_profile(name: str, embedding: np.ndarray):
    """Save a speaker's voiceprint profile."""
    if embedding is None:
        logger.error(f"Cannot save profile for {name}: invalid embedding")
        return False
    
    try:
        profile_path = os.path.join(PROFILE_DIR, f"{name}.npy")
        np.save(profile_path, embedding)
        logger.success(f"Saved voice profile: {name}")
        return True
    except Exception as e:
        logger.error(f"Failed to save profile {name}: {e}")
        return False


def load_profiles() -> dict:
    """Load all stored voice profiles."""
    profiles = {}
    try:
        for f in os.listdir(PROFILE_DIR):
            if f.endswith(".npy"):
                name = f.replace(".npy", "")
                profile_path = os.path.join(PROFILE_DIR, f)
                profiles[name] = np.load(profile_path)
        logger.debug(f"Loaded {len(profiles)} voice profiles")
        return profiles
    except Exception as e:
        logger.error(f"Failed to load profiles: {e}")
        return {}


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Calculate cosine similarity between two embeddings."""
    magnitude_a = np.linalg.norm(a)
    magnitude_b = np.linalg.norm(b)
    
    if magnitude_a == 0 or magnitude_b == 0:
        return 0.0
    
    return np.dot(a, b) / (magnitude_a * magnitude_b)


def identify(wav_path: str) -> tuple:
    """
    Identify speaker from audio file.
    
    Args:
        wav_path: Path to WAV file
        
    Returns:
        (speaker_name, confidence_score)
        Returns ("unknown", score) if below threshold
    """
    if _get_encoder() is None:
        logger.warning("Voice encoder not available, returning unknown")
        return "unknown", 0.0
    
    embedding = embed_wav(wav_path)
    if embedding is None:
        return "unknown", 0.0
    
    profiles = load_profiles()
    if not profiles:
        logger.warning("No voice profiles loaded")
        return "unknown", 0.0
    
    best_name, best_score = None, 0.0
    
    for name, ref_embedding in profiles.items():
        score = cosine_similarity(embedding, ref_embedding)
        if score > best_score:
            best_name, best_score = name, score
    
    # Check if match exceeds threshold
    if best_score >= THRESHOLD:
        logger.success(f"Identified speaker: {best_name} ({best_score:.3f})")
        return best_name, float(best_score)
    else:
        logger.warning(f"Speaker not recognized (best: {best_name} {best_score:.3f})")
        return "unknown", float(best_score)


def get_all_speakers() -> list:
    """Get list of enrolled speakers."""
    profiles = load_profiles()
    return list(profiles.keys())
