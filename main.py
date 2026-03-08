import os
import time
import speech_recognition as sr
import pyttsx3
import json
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_BASE = os.getenv("OPENAI_API_BASE", "http://localhost:8002/v1")
API_KEY = os.getenv("OPENAI_API_KEY", "local")
MODEL_NAME = os.getenv("MODEL_NAME", "qwen2.5:3b-instruct")
SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT", "You are a helpful voice assistant. Answer in 1-2 short sentences.")

# Initialize OpenAI Client (connecting to local LLM server)
client = OpenAI(base_url=API_BASE, api_key=API_KEY)

# Initialize TTS Engine
tts_engine = pyttsx3.init()
# Configure preferred voice properties (can adjust rate/volume as needed)
tts_engine.setProperty('rate', 160)

def speak(text):
    """Speaks the text out loud using pyttsx3."""
    print(f"\n[Qwen] {text}")
    tts_engine.say(text)
    tts_engine.runAndWait()

def query_llm(prompt):
    """Sends the user prompt to the local Qwen model and returns the response."""
    print(f"\n[Thinking...] Sending to {API_BASE}")
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=150
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"\n[Error] LLM request failed: {e}")
        return "I'm sorry, I couldn't connect to my brain. Is the local LLM running?"

def main():
    print("="*50)
    print(" Voice Agent Initializing...")
    print(f" LLM Endpoint: {API_BASE}")
    print(f" Model Name: {MODEL_NAME}")
    print("="*50)
    print("\n[System] Initializing Microphone...")
    
    r = sr.Recognizer()
    # Wait for a longer pause before considering the phrase complete
    r.pause_threshold = 1.5
    mic = sr.Microphone()
    
    # Adjust for ambient noise briefly
    with mic as source:
        r.adjust_for_ambient_noise(source, duration=1)
        
    speak("Initialization complete. I am ready. What is on your mind?")
    
    while True:
        try:
            with mic as source:
                print("\n[Listening...] (Say 'exit' to quit)")
                # listen() blocks until a phrase starts and finishes
                audio = r.listen(source, timeout=None, phrase_time_limit=10)
                
            print("\n[Recognizing...]")
            # Using Vosk offline STT
            # The first time this runs, it will download a ~40MB Vosk model to your PC
            text = r.recognize_vosk(audio)
            
            if not text or not text.strip():
                continue
                
            print(f"\n[You] {text}")
            
            # Simple exit command
            if text.lower() in ["exit", "quit", "stop listening", "goodbye"]:
                speak("Goodbye! Shutting down.")
                break
                
            # Query Model
            llm_response = query_llm(text)
            
            # Speak Response
            speak(llm_response)
            
        except sr.UnknownValueError:
            print("\n[System] Could not understand audio.")
        except sr.WaitTimeoutError:
            pass
        except sr.RequestError as e:
            print(f"\n[System] Recognition request failed: {e}")
        except KeyboardInterrupt:
            print("\n[System] Stopping...")
            break
        except Exception as e:
            print(f"\n[System] An error occurred: {e}")

if __name__ == "__main__":
    main()
