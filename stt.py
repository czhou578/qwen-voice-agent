import os
import io
import numpy as np
import speech_recognition as sr
from faster_whisper import WhisperModel

class STTManager:
    def __init__(self):
        print("\n[System] Loading Faster-Whisper Model (base.en)...")
        # Run on CPU with int8 quantization for speed on typical desktop CPUs
        self.model = WhisperModel("base.en", device="cpu", compute_type="int8")
        
        print("[System] Initializing Microphone...")
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 300  # Adjust if it's too sensitive or not sensitive enough
        self.recognizer.dynamic_energy_threshold = False
        
        # Increase pause threshold so it doesn't aggressively cut off the end of your sentence
        # if you pause slightly before saying "YouTube"
        self.recognizer.pause_threshold = 1.5
        self.recognizer.non_speaking_duration = 0.5
        
        self.microphone = sr.Microphone(sample_rate=16000)
        
        # Adjust for ambient noise once on startup
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            
        self.is_listening = False
        self._stop_listening_func = None

    def start_listening(self):
        self.is_listening = True

    def pause_listening(self):
        self.is_listening = False
        
    def reset(self):
        pass

    def listen_for_speech(self):
        """Blocks and yields text once recognized."""
        if not self.is_listening:
            self.start_listening()
        with self.microphone as source:
            while self.is_listening:
                try:
                    # Listen for a single phrase (blocks until silence is detected)
                    audio_data = self.recognizer.listen(source, timeout=1, phrase_time_limit=15)
                    
                    if not self.is_listening:
                        break # In case we got paused while waiting for speech
                        
                    # Convert the raw audio bytes directly into a normalized float32 numpy array
                    # Whisper expects 16kHz audio, which our sr.Microphone is already set to
                    audio_np = np.frombuffer(audio_data.get_raw_data(), dtype=np.int16).astype(np.float32) / 32768.0
                    
                    # Transcribe
                    segments, _ = self.model.transcribe(audio_np, beam_size=5, condition_on_previous_text=False)
                    
                    text = "".join([segment.text for segment in segments]).strip()
                    
                    if text:
                        return text
                        
                except sr.WaitTimeoutError:
                    # Just loops around and keeps listening if nobody spoke
                    pass
                except Exception as e:
                    print(f"\n[STT Error] {e}")
