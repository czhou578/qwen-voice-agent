import os
import sys
import time
import json
import queue
import threading
import pyttsx3
import pyaudio
from vosk import Model, KaldiRecognizer
from openai import OpenAI
from dotenv import load_dotenv

# can pause and replay youtube videos on command
# add emotion 
# improve latency
# find better tts module
# modularize the code so that a pipeline can be created for different models

# Load environment variables
load_dotenv()

API_BASE = os.getenv("OPENAI_API_BASE", "http://localhost:8002/v1")
API_KEY = os.getenv("OPENAI_API_KEY", "local")
MODEL_NAME = os.getenv("MODEL_NAME", "qwen2.5:3b-instruct")
SYSTEM_PROMPT = """You are a helpful voice assistant named Qwen. 
If the user asks you to search the web or look something up on Google, you MUST reply ONLY with the exact format:
[SEARCH] query here

If the user asks you to search specifically on YouTube, you MUST reply ONLY with the exact format:
[YOUTUBE] query here

If the user asks you to navigate to, go to, or open a specific website or URL, you MUST reply ONLY with the exact format:
[NAVIGATE] example.com

For all other general questions or conversation, answer verbally in 1-2 short, natural sentences without abbreviations. Do not use emojis, lists, or code formatting."""

# Initialize OpenAI Client (connecting to local LLM server)
client = OpenAI(base_url=API_BASE, api_key=API_KEY)

# Initialize Background TTS Queue
tts_queue = queue.Queue()

def tts_worker():
    """Background thread for continuous Text-to-Speech processing."""
    PIPER_MODEL_PATH = "en_US-lessac-medium.onnx"
    use_piper = False
    
    try:
        if os.path.exists(PIPER_MODEL_PATH):
            from piper.voice import PiperVoice
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
                import sounddevice as sd
                import numpy as np
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

def query_llm_stream(prompt):
    """Sends the prompt to LLM, streams the response, and chunks it into sentences for immediate playback."""
    print(f"\n[Thinking...] Sending to {API_BASE}")
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=150,
            stream=True
        )
        
        sentence_buffer = ""
        full_response = ""
        
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                word = chunk.choices[0].delta.content
                sentence_buffer += word
                full_response += word
                
                # If first character is [, this is a command. We don't speak anything yet, let it buffer fully.
                if full_response.strip().startswith("["):
                    continue
                
                # Simple sentence boundary detection
                if any(punct in word for punct in ['.', '!', '?']):
                    if sentence_buffer.strip():
                        speak(sentence_buffer.strip())
                        sentence_buffer = ""
                        
        # Flush remaining text if it wasn't a command
        if sentence_buffer.strip() and not full_response.strip().startswith("["):
            speak(sentence_buffer.strip())
            
        return full_response.strip()
    except Exception as e:
        print(f"\n[Error] LLM request failed: {e}")
        speak("I'm sorry, I couldn't connect to my brain.")
        return ""

def get_vosk_model_path():
    """Gets the path to the downloaded Vosk model from speech_recognition library."""
    import speech_recognition as sr
    base_dir = os.path.dirname(sr.__file__)
    model_path = os.path.join(base_dir, "models", "vosk")
    if not os.path.exists(model_path):
        print(f"Error: Vosk model not found at {model_path}.")
        print("Please run: sprc download vosk")
        sys.exit(1)
    return model_path

def main():
    print("="*50)
    print(" Voice Agent Initializing (Low-Latency Mode)...")
    print(f" LLM Endpoint: {API_BASE}")
    print(f" Model Name: {MODEL_NAME}")
    print("="*50)
    
    print("\n[System] Loading Vosk STT Model...")
    model_path = get_vosk_model_path()
    model = Model(model_path)
    # 16000Hz mono is required by Vosk
    recognizer = KaldiRecognizer(model, 16000)
    
    print("\n[System] Initializing Microphone...")
    audio = pyaudio.PyAudio()
    stream = audio.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=4000)
    stream.start_stream()
    
    speak("I am ready!")
    # Wait for the initial "I am ready!" to finish speaking
    tts_queue.join()
    
    print("\n[Listening...] (Say 'exit' to quit)")
    
    while True:
        try:
            # Read small chunks of audio (latency optimization)
            data = stream.read(4000, exception_on_overflow=False)
            
            # AcceptWaveform returns True when a silence boundary is detected, marking phrase completion
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                text = result.get("text", "")
                
                if not text or not text.strip():
                    continue
                    
                print(f"\n[You] {text}")
                
                # Simple exit command
                if text.lower() in ["exit", "quit", "stop listening", "goodbye"]:
                    speak("Goodbye! Shutting down.")
                    tts_queue.join()
                    break
                
                # Pause mic stream while processing and speaking to avoid hearing itself
                stream.stop_stream()
                
                # Query Model (Streams instantly to TTS)
                llm_response = query_llm_stream(text)
                
                # Check for Browser Commands (Since we suppressed TTS via full_response.startswith("["))
                if "[YOUTUBE]" in llm_response:
                    query = llm_response.replace("[YOUTUBE]", "").strip()
                    speak(f"Okay, pulling up {query} on YouTube.")
                    import browser_tools
                    browser_tools.search_youtube(query)

                elif "[SEARCH]" in llm_response:
                    query = llm_response.replace("[SEARCH]", "").strip()
                    speak(f"Okay, I am searching Google for {query}")
                    import browser_tools
                    browser_tools.search_google(query)
                    
                elif "[NAVIGATE]" in llm_response:
                    url = llm_response.replace("[NAVIGATE]", "").strip()
                    speak(f"Okay, I am opening {url}")
                    import browser_tools
                    browser_tools.navigate_to(url)
                
                # Wait for TTS to finish speaking the entire response before listening again
                tts_queue.join()
                
                # Clear out any stale audio that arrived before we paused the stream
                recognizer.Reset()
                
                # Restart listening
                stream.start_stream()
                print("\n[Listening...] (Say 'exit' to quit)")
                
        except KeyboardInterrupt:
            print("\n[System] Stopping...")
            import browser_tools
            try:
                browser_tools.cleanup()
            except:
                pass
            sys.exit(0)
        except Exception as e:
            print(f"\n[System] An error occurred: {e}")

if __name__ == "__main__":
    main()
