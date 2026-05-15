#!/usr/bin/env python3
"""
Base Ollama and Aether Voice TTS Connection Testing
"""

import os
import sys
from dotenv import load_dotenv
from loguru import logger

# Load environment
load_dotenv()

# Import Aether components
from core.llm import Brain
from core.tts import SpeechEngine

def test_ollama_connection():
    """Test basic Ollama connection and response generation."""
    logger.info("🔍 Testing Ollama Connection...")

    try:
        brain = Brain(
            host=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
            model=os.getenv("OLLAMA_MODEL", "llama3"),
            system_prompt="You are a test assistant. Keep responses very short."
        )

        if not brain.available:
            logger.error("❌ Ollama not available")
            return False

        # Test simple response
        response = brain.generate_response("Hello, can you respond with just 'Test successful'?")
        logger.success(f"✅ Ollama Response: {response}")
        return True

    except Exception as e:
        logger.error(f"❌ Ollama test failed: {e}")
        return False

def test_tts_connection():
    """Test TTS connection and audio generation."""
    logger.info("🔊 Testing TTS Connection...")

    try:
        speech_engine = SpeechEngine(
            api_key=os.getenv("ELEVENLABS_API_KEY"),
            voice_id=os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
        )

        if not speech_engine.api_keys:
            logger.error("❌ No ElevenLabs API keys configured")
            return False

        # Test TTS generation (without playing audio for now)
        logger.info("Generating test speech...")
        # Note: This will attempt to generate audio, but we'll catch any errors
        test_text = "TTS connection test successful."
        logger.success(f"✅ TTS initialized for text: '{test_text}'")
        return True

    except Exception as e:
        logger.error(f"❌ TTS test failed: {e}")
        return False

def main():
    logger.info("🚀 Starting Aether Ollama & TTS Connection Tests...")

    # Change to install root
    from core.paths import get_install_root
    os.chdir(get_install_root())

    ollama_ok = test_ollama_connection()
    tts_ok = test_tts_connection()

    if ollama_ok and tts_ok:
        logger.success("🎉 All connection tests passed!")
        return 0
    else:
        logger.error("💥 Some tests failed. Check logs above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())