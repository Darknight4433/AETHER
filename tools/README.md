# Aether Tools

Quick utilities for Aether system setup and management.

## Voice Enrollment

### Purpose
Record your voice and create a unique voiceprint for speaker identification. Aether will recognize when YOU are speaking vs. unknown speakers, enabling identity-based permissions.

### Quick Start

1. **Record your voiceprint:**
```bash
python tools/enroll.py vaish
```

Replace `vaish` with your name (alphanumeric only, no spaces).

2. **Follow the prompts:**
   - Microphone device will be auto-detected
   - You'll record for ~10 seconds
   - Speak naturally and clearly
   - Use similar tone/speed as normal speech

3. **Verify enrollment:**
   - Profile saved to: `data/voice_profiles/vaish.npy`
   - You're ready to use authenticated commands

### Important Notes

- **One profile per person**: Run the tool once per user
- **Same environment**: Record in the environment where you'll use Aether daily
- **Natural speech**: Don't over-enunciate or change your voice
- **Mic quality**: Cleaner audio = better accuracy

### Adding More Users

```bash
python tools/enroll.py guest      # Guest profile
python tools/enroll.py family     # Family member
```

Then update `core/permissions.py` to authorize them:

```python
AUTHORIZED_USERS = ["vaish", "guest"]  # Add guest for critical actions
```

### Troubleshooting

**"No sound recorded"**
- Check microphone is working: `python -c "import sounddevice as sd; sd.default.samplerate = 16000"`
- Try a different microphone with `-d` flag (future enhancement)

**"Bad voice match after enrollment"**
- Re-enroll with clearer audio
- Adjust THRESHOLD in `core/voice_id.py` (0.70-0.85)

**"Always matches as unknown"**
- Check profile file exists: `ls data/voice_profiles/`
- Re-enroll with microphone placed at same distance

### How Voice Recognition Works

1. **Enrollment**: Your voice recorded → 256-dim embedding → saved
2. **Recognition**: New voice → embedding → compared to profiles → identified
3. **Permissions**: Safe actions allowed for anyone; risky actions only for you
4. **Latency**: ~100-300ms (no cloud latency)

### Advanced

**Tuning similarity threshold:**
Edit `core/voice_id.py`:
```python
THRESHOLD = 0.75  # Range: 0.70 (loose) to 0.85 (strict)
```

**Multiple samples for better accuracy:**
Enroll 2-3 times and average embeddings (future enhancement).

## Overlay Testing

### Purpose
Test the microphone LED overlay that shows Aether's current state as a colored dot in the top-right corner of your screen.

### Quick Test

```bash
python tools/test_overlay.py
```

This will:
- Start the overlay in the background
- Cycle through all states (idle → listening → thinking → speaking → idle)
- Show a colored dot in the top-right corner
- Each state displays for 2 seconds

### Color Guide

- 🔵 **Blue**: Idle (faint, always visible)
- 🟢 **Green**: Listening (microphone active)
- 🟡 **Yellow**: Thinking (processing request)
- 🔴 **Red**: Speaking (responding)

### Manual Testing

You can also test manually:

```python
from core.overlay import start_overlay
from ui.state import state

# Start overlay
start_overlay()

# Change states
state["status"] = "listening"  # Green dot
state["status"] = "thinking"   # Yellow dot
state["status"] = "speaking"   # Red dot
state["status"] = "idle"       # Blue dot
```

### Customization

**Change position:**
Edit `core/overlay.py` in the `__init__` method:
```python
x = screen_width - self.width - 15  # Margin from right
y = 15  # Margin from top
```

**Change size:**
```python
self.width, self.height = 30, 30  # Bigger dot
```

**Always hide when idle:**
Change the `update_color` method to hide instead of showing faint blue.

### Troubleshooting

**"No dot visible"**
- Check if Tkinter is working: `python -c "import tkinter; tk.Tk()"`
- Make sure no other always-on-top windows are covering it
- Try running as administrator

**"Dot not updating colors"**
- Verify state is being updated: `print(state["status"])`
- Check that overlay thread is running

**"Performance issues"**
- The overlay updates every 100ms - increase to 250ms if needed
- Reduce transparency: `self.root.attributes("-alpha", 1.0)`
