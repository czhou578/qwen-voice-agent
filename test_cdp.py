import os
from playwright.sync_api import sync_playwright

def test_cdp():
    with sync_playwright() as p:
        debug_port = os.getenv("BRAVE_DEBUG_PORT", "9222")
        cdp_url = f"http://localhost:{debug_port}"
        
        try:
            print(f"Connecting to {cdp_url}...")
            browser = p.chromium.connect_over_cdp(cdp_url)
            print(f"Connected! Contexts: {len(browser.contexts)}")
            
            if browser.contexts:
                context = browser.contexts[0]
                print(f"Using existing context. Pages: {len(context.pages)}")
            else:
                print("No contexts found. Creating new context.")
                context = browser.new_context()
            
            print("Creating new page (tab)...")
            page = context.new_page()
            print("Navigating to example.com...")
            page.goto("https://example.com")
            print("Success! Sleeping 2 seconds...")
            import time
            time.sleep(2)
            print("Done")
            
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_cdp()
