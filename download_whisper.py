import sys
from faster_whisper import WhisperModel
import logging

logging.basicConfig(level=logging.INFO)

print("Downloading and initializing Faster-Whisper base.en model...")
print("This may take several minutes depending on your internet connection.")
model = WhisperModel("base.en", device="cpu", compute_type="int8")
print("Model initialized successfully!")
sys.exit(0)
