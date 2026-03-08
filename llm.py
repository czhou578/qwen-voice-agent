import os
import time
from openai import OpenAI
from tts import speak

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

try:
    client = OpenAI(base_url=API_BASE, api_key=API_KEY)
except Exception as e:
    print(f"[Error] Failed to initialize OpenAI client: {e}")
    client = None

def prewarm_llm():
    """Sends a silent request to the LLM to force it into VRAM before the user speaks."""
    if not client: return
    print(f"\n[System] Waking up LLM ({MODEL_NAME}) into VRAM...")
    try:
        client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": "wake up"}],
            max_tokens=1
        )
        print("[System] LLM is fully loaded and ready.")
    except Exception as e:
        print(f"[System] LLM wake-up failed: {e}")

def query_llm_stream(prompt):
    """Sends the prompt to LLM, streams the response, and chunks it into sentences for immediate playback."""
    if not client: return ""
    print(f"\n[Thinking...] Sending to {API_BASE}")
    start_time = time.time()
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
        got_first_token = False
        
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                if not got_first_token:
                    ttft = time.time() - start_time
                    print(f"\n[Telemetry] Time to First Token (TTFT): {ttft:.2f} seconds")
                    got_first_token = True
                    
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
