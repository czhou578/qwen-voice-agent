from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import os
import webbrowser
import urllib.parse

load_dotenv()

class BrowserManager:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.cdp_connected = False
    
    def start(self):
        """Initializes or connects to the browser instance."""
        if not self.playwright:
            print("[Browser] Starting Playwright...")
            self.playwright = sync_playwright().start()
            
            # Try to connect to an existing running Brave instance
            debug_port = os.getenv("BRAVE_DEBUG_PORT", "9222")
            cdp_url = f"http://127.0.0.1:{debug_port}"
            
            try:
                print(f"[Browser] Attempting to connect to CDP at {cdp_url}...")
                self.browser = self.playwright.chromium.connect_over_cdp(cdp_url, timeout=3000)
                print("[Browser] Connected to existing Brave instance via CDP!")
                self.context = self.browser.contexts[0] if self.browser.contexts else self.browser.new_context()
                self.page = self.context.new_page()
                self.cdp_connected = True
                return True
            except Exception as e:
                print(f"[Browser] CDP connection failed: {e}")
                print("[Browser] Playwright cannot control the existing window. Falling back to OS native tabs.")
                self.cdp_connected = False
                return False
            
    def close(self):
        """Closes the browser instance."""
        if self.playwright:
            print("[Browser] Cleaning up Playwright...")
            if self.context and self.cdp_connected:
                try: self.context.close()
                except: pass
            if self.browser and self.cdp_connected:
                try: self.browser.close()
                except: pass
            self.playwright.stop()
            self.playwright = None
            self.cdp_connected = False

    def get_page(self):
        """Returns the active page, starting the browser if necessary."""
        if not self.cdp_connected or not self.page or self.page.is_closed():
            success = self.start()
            if not success:
                return None
        return self.page

# Global singleton to keep the browser alive between commands
_manager = BrowserManager()

def search_google(query: str):
    """Navigates to Google and searches the query."""
    print(f"[Browser Tools] Searching Google for: {query}")
    page = _manager.get_page()
    
    if page:
        try:
            page.goto("https://www.google.com")
            search_box = page.locator("textarea[name='q'], input[name='q']").first
            search_box.fill(query)
            search_box.press("Enter")
            page.wait_for_load_state("networkidle", timeout=5000)
            return f"Successfully searched Google for {query}."
        except Exception as e:
            print(f"[Browser Error] {e}")
            return "Sorry, I failed to search Google via Playwright."
    else:
        # Fallback to OS native tab opening
        print("[Browser Tools] Using OS native browser to open new tab.")
        url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
        webbrowser.open(url)
        return f"Successfully searched Google for {query} natively."

def navigate_to(url: str):
    """Navigates the browser to the exact URL provided."""
    print(f"[Browser Tools] Navigating to: {url}")
    if not url.startswith("http"):
        url = "https://" + url
        
    page = _manager.get_page()
    if page:
        try:
            page.goto(url)
            page.wait_for_load_state("networkidle", timeout=5000)
            return f"Successfully navigated to {url}."
        except Exception as e:
            print(f"[Browser Error] {e}")
            return f"Sorry, I failed to navigate to {url} via Playwright."
    else:
        # Fallback to OS native tab opening
        print("[Browser Tools] Using OS native browser to open new tab.")
        webbrowser.open(url)
        return f"Successfully navigated to {url} natively."

def search_youtube(query: str):
    """Navigates to YouTube and searches the query."""
    print(f"[Browser Tools] Searching YouTube for: {query}")
    page = _manager.get_page()
    
    if page:
        try:
            page.goto("https://www.youtube.com")
            search_box = page.locator("input[name='search_query']").first
            search_box.wait_for(state="visible", timeout=10000)
            search_box.fill(query)
            search_box.press("Enter")
            page.wait_for_load_state("networkidle", timeout=5000)
            return f"Successfully searched YouTube for {query}."
        except Exception as e:
            print(f"[Browser Error] {e}")
            return "Sorry, I failed to search YouTube via Playwright."
    else:
        # Fallback
        print("[Browser Tools] Using OS native browser to open new tab.")
        url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
        webbrowser.open(url)
        return f"Successfully searched YouTube for {query} natively."

def replay_youtube():
    """Restarts the currently playing YouTube video from the beginning."""
    print("[Browser Tools] Replaying YouTube Video")
    page = _manager.get_page()
    
    if page:
        try:
            if "youtube.com/watch" not in page.url:
                print("[Browser Error] Not currently watching a YouTube video.")
                return "Sorry, I am not currently on a YouTube video page."
                
            page.evaluate("""
                const video = document.querySelector('video');
                if (video) {
                    video.currentTime = 0;
                    video.play();
                }
            """)
            return "Successfully restarted the YouTube video."
        except Exception as e:
            print(f"[Browser Error] {e}")
            return "Sorry, I failed to restart the YouTube video."
    else:
        print("[Browser Error] CDP not connected. Cannot interact with the YouTube player.")
        return "I can only replay videos if you launch your browser with the debugging port enabled."

def click_first_youtube_result():
    """Clicks the first video in the YouTube search results."""
    print("[Browser Tools] Clicking first YouTube result")
    page = _manager.get_page()
    
    if page:
        try:
            if "youtube.com/results" not in page.url:
                print("[Browser Error] Not currently on a YouTube search page.")
                return "I must be on a YouTube search page to do this."
                
            # Click the first video thumbnail
            first_video = page.locator("ytd-video-renderer a#thumbnail").first
            first_video.click()
            page.wait_for_load_state("networkidle", timeout=5000)
            return "Successfully clicked the first YouTube video."
        except Exception as e:
            print(f"[Browser Error] {e}")
            return "Sorry, I failed to click the first YouTube video."
    else:
        print("[Browser Error] CDP not connected.")
        return "I can only click videos if you launch your browser with the debugging port enabled."

def cleanup():
    """Called on exit to close the browser."""
    _manager.close()
