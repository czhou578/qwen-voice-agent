import sys
from dotenv import load_dotenv

# can pause and replay youtube videos on command
# add emotion 
# improve latency
# find better tts module
# modularize the code so that a pipeline can be created for different models

# Load environment variables FIRST before importing custom modules
load_dotenv()

from llm import prewarm_llm, query_llm_stream, API_BASE, MODEL_NAME
from tts import speak, wait_for_tts
from stt import STTManager
import browser_tools

def main():
    print("="*50)
    print(" Voice Agent Initializing (Modular Pipeline)...")
    print(f" LLM Endpoint: {API_BASE}")
    print(f" Model Name: {MODEL_NAME}")
    print("="*50)
    
    stt = STTManager()
    
    # Pre-warm the LLM so the first query has zero cold-start delay
    prewarm_llm()
    
    # Ready to go
    stt.start_listening()
    speak("I am ready!")
    wait_for_tts()
    
    print("\n[Listening...] (Say 'exit' to quit)")
    
    while True:
        try:
            # Re-start listening if paused
            stt.start_listening()
            text = stt.listen_for_speech()
            print(f"\n[You] {text}")
            
            # Simple exit command
            if text.lower() in ["exit", "quit", "stop listening", "goodbye"]:
                speak("Goodbye! Shutting down.")
                wait_for_tts()
                break
            
            # Pause mic stream while processing and speaking to avoid hearing itself
            stt.pause_listening()
            
            # Query Model (Streams instantly to TTS)
            llm_response = query_llm_stream(text)
            
            # Check for Browser Commands
            if "[YOUTUBE]" in llm_response:
                query = llm_response.replace("[YOUTUBE]", "").strip()
                speak(f"Okay, pulling up {query} on YouTube.")
                browser_tools.search_youtube(query)

            elif "[SEARCH]" in llm_response:
                query = llm_response.replace("[SEARCH]", "").strip()
                speak(f"Okay, I am searching Google for {query}")
                browser_tools.search_google(query)
                
            elif "[NAVIGATE]" in llm_response:
                url = llm_response.replace("[NAVIGATE]", "").strip()
                speak(f"Okay, I am opening {url}")
                browser_tools.navigate_to(url)
            
            # Wait for TTS to finish speaking the entire response before listening again
            wait_for_tts()
            
            # Clear out any stale audio that arrived before we paused the stream
            stt.reset()
            
            print("\n[Listening...] (Say 'exit' to quit)")
            
        except KeyboardInterrupt:
            print("\n[System] Stopping...")
            try:
                browser_tools.cleanup()
            except:
                pass
            sys.exit(0)
        except Exception as e:
            print(f"\n[System] An error occurred: {e}")

if __name__ == "__main__":
    main()
