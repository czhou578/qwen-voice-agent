import queue
import threading
import os
import pyttsx3
import sounddevice as sd
import numpy as np  
from piper.voice import PiperVoice

tts_queue = queue.Queue()

def tts_worker():
    """Background thread for continuous Text-to-Speech processing."""
    PIPER_MODEL_PATH = "en_US-lessac-medium.onnx"
    use_piper = False
    
    try:
        if os.path.exists(PIPER_MODEL_PATH):
            piper_engine = PiperVoice.load(PIPER_MODEL_PATH)
            piper_sample_rate = piper_engine.config.sample_rate
            use_piper = True
            print("[System] Loaded Piper TTS Model.")
        else:
            raise FileNotFoundError("Piper model not found locally.")
    except Exception as e:
        print(f"[System] Piper error fallback to pyttsx3: {e}")
        # We must initialize pyttsx3 inside the thread loop for safety in some OS environments
        tts_engine = pyttsx3.init()
        tts_engine.setProperty('rate', 160)
        
    while True:
        text = tts_queue.get()
        if text is None:
            break
            
        print(f"\n[Qwen] {text}")
        
        if use_piper:
            try:
                stream = sd.OutputStream(samplerate=piper_sample_rate, channels=1, dtype='int16')
                stream.start()
                for chunk in piper_engine.synthesize(text):
                    stream.write(chunk.audio_int16_array)
                stream.stop()
                stream.close()
            except Exception as e:
                print(f"[System] Piper playback failed: {e}")
        else:
            tts_engine.say(text)
            tts_engine.runAndWait()
            
        tts_queue.task_done()

# Start TTS background thread
tts_thread = threading.Thread(target=tts_worker, daemon=True)
tts_thread.start()

def speak(text):
    """Puts text into the TTS queue to be spoken immediately."""
    tts_queue.put(text)

def wait_for_tts():
    """Blocks until all queued speech has finished playing."""
    tts_queue.join()
