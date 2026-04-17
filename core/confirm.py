def confirm_and_execute(suggestion, executor, speech_engine, audio_interface):
    speech_engine.speak_async(f"{suggestion['reason']}. Should I proceed?")
    
    # Block and wait for mic translation natively via Whisper integration
    user_text = audio_interface.listen_and_transcribe()
    
    if user_text:
        ans = user_text.lower()
        if "yes" in ans or "sure" in ans or "do it" in ans or "ok" in ans:
            return executor(suggestion["action"], suggestion["args"])
        if "no" in ans or "stop" in ans or "skip" in ans:
            return "❌ Skipped"
            
    return "⏳ No response, skipped"
