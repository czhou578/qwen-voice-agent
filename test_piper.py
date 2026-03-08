import sys
from piper.voice import PiperVoice
import sounddevice as sd
import numpy as np

model_path = "en_US-lessac-medium.onnx"

print(f"Loading {model_path}...")
voice = PiperVoice.load(model_path)

print("Synthesizing audio...")
text = "Hello there. I am Piper, a much better and faster voice than pyttsx3."
sample_rate = voice.config.sample_rate

print(f"Sample rate is {sample_rate}")
stream = sd.OutputStream(samplerate=sample_rate, channels=1, dtype='int16')
stream.start()

for audio_bytes in voice.synthesize_stream_raw(text):
    audio_data = np.frombuffer(audio_bytes, dtype=np.int16)
    stream.write(audio_data)

stream.stop()
stream.close()
print("Done playing!")
