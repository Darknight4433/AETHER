#!/usr/bin/env python3
"""
Test script for the microphone LED overlay.
Shows how the overlay changes colors based on state.
"""

import sys
import os
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.overlay import start_overlay
from ui.state import state
from loguru import logger

def test_overlay():
    """Test the overlay by cycling through different states."""
    print("🎯 Testing Microphone LED Overlay")
    print("=" * 40)

    # Start overlay in background
    print("Starting overlay...")
    start_overlay()

    # Give overlay time to initialize
    time.sleep(1)

    print("Cycling through states...")
    print("Watch the top-right corner of your screen!")

    states_to_test = [
        ("idle", "🔵 Blue (idle)"),
        ("listening", "🟢 Green (listening)"),
        ("thinking", "🟡 Yellow (thinking)"),
        ("speaking", "🔴 Red (speaking)"),
        ("idle", "🔵 Blue (back to idle)")
    ]

    for status, description in states_to_test:
        print(f"Setting state: {description}")
        state["status"] = status
        time.sleep(2)  # Show each state for 2 seconds

    print("\n✅ Overlay test complete!")
    print("The overlay should show a small colored dot in the top-right corner.")
    print("Press Ctrl+C to exit.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Test finished!")

if __name__ == "__main__":
    test_overlay()