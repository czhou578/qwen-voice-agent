import os
import sys
import pyaudio
import json
from vosk import Model, KaldiRecognizer

def get_vosk_model_path():
    """Gets the path to the downloaded Vosk model from speech_recognition library."""
    try:
        import speech_recognition as sr
        base_dir = os.path.dirname(sr.__file__)
        model_path = os.path.join(base_dir, "models", "vosk")
        if not os.path.exists(model_path):
            raise FileNotFoundError()
        return model_path
    except Exception:
        print("Error: Vosk model not found.")
        print("Please run: sprc download vosk")
        sys.exit(1)

class STTManager:
    def __init__(self):
        print("\n[System] Loading Vosk STT Model...")
        model_path = get_vosk_model_path()
        self.model = Model(model_path)
        self.recognizer = KaldiRecognizer(self.model, 16000)
        
        print("[System] Initializing Microphone...")
        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=4000)
        self.is_listening = False

    def start_listening(self):
        self.stream.start_stream()
        self.is_listening = True

    def pause_listening(self):
        self.stream.stop_stream()
        self.is_listening = False
        
    def reset(self):
        self.recognizer.Reset()

    def listen_for_speech(self):
        """Blocks and yields text once recognized."""
        if not self.is_listening:
            self.start_listening()
            
        while True:
            # Read small chunks of audio
            data = self.stream.read(4000, exception_on_overflow=False)
            
            # AcceptWaveform returns True when a silence boundary is detected, marking phrase completion
            if self.recognizer.AcceptWaveform(data):
                result = json.loads(self.recognizer.Result())
                text = result.get("text", "")
                
                if text and text.strip():
                    return text.strip()
