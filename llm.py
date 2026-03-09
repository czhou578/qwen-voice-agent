import os
import time
from openai import OpenAI
from tts import speak

API_BASE = os.getenv("OPENAI_API_BASE", "http://localhost:8002/v1")
API_KEY = os.getenv("OPENAI_API_KEY", "local")
MODEL_NAME = os.getenv("MODEL_NAME", "qwen2.5:3b-instruct")

SYSTEM_PROMPT = """You are a helpful voice assistant named Qwen. 
You must strictly follow these exact command formats for actions:

- To search Google: [SEARCH] query here
- To search YouTube: [YOUTUBE] query here
- To restart a YouTube video: [YOUTUBE_REPLAY]
- To play the first YouTube video result: [YOUTUBE_CLICK_FIRST]
- To open a website: [NAVIGATE] example.com

Example 1:
User: "Search for cat videos on YouTube"
Assistant: [YOUTUBE] cat videos

Example 2:
User: "Go to reddit"
Assistant: [NAVIGATE] reddit.com

Example 3:
User: "How are you today?"
Assistant: I am doing well, thank you!

For general questions, answer verbally in 1-2 short, natural sentences without abbreviations. 
IMPORTANT RULE: When you output a command, you MUST NOT output any other text. Output literally ONLY the command format. Do NOT invent new brackets."""

chat_history = []

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
    """Sends the prompt to LLM with history, streams response, and chunks into sentences for playback."""
    global chat_history
    if not client: return ""
    print(f"\n[Thinking...] Sending to {API_BASE}")
    start_time = time.time()
    
    # Construct messages with system prompt, history, and current prompt
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(chat_history)
    messages.append({"role": "user", "content": prompt})
    
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
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
                
                # If response contains a [, it's likely a command sequence. Suppress speech immediately.
                if "[" in full_response:
                    continue
                
                # Simple sentence boundary detection
                if any(punct in word for punct in ['.', '!', '?']):
                    if sentence_buffer.strip():
                        speak(sentence_buffer.strip())
                        sentence_buffer = ""
                        
        # Flush remaining text if it wasn't a command
        if sentence_buffer.strip() and "[" not in full_response:
            speak(sentence_buffer.strip())
            
        full_response_clean = full_response.strip()
        
        # Save to history (keep last 10 interactions to avoid token overflow)
        chat_history.append({"role": "user", "content": prompt})
        chat_history.append({"role": "assistant", "content": full_response_clean})
        if len(chat_history) > 20:
            chat_history = chat_history[-20:]
            
        print(f"\n[LLM Debug Raw Output]: '{full_response_clean}'")
        return full_response_clean
    except Exception as e:
        print(f"\n[Error] LLM request failed: {e}")
        speak("I'm sorry, I couldn't connect to my brain.")
        return ""
