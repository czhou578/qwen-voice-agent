from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import os

load_dotenv()

class BrowserManager:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
    
    def start(self):
        """Initializes or connects to the browser instance."""
        if not self.playwright:
            self.playwright = sync_playwright().start()
            
            # 1. Try to connect to an existing running Brave instance
            debug_port = os.getenv("BRAVE_DEBUG_PORT", "9222")
            cdp_url = f"http://127.0.0.1:{debug_port}"
            
            try:
                # This will connect to your currently open Brave browser (if it was launched with debugging on)
                self.browser = self.playwright.chromium.connect_over_cdp(cdp_url)
                print("[Browser] Connected to existing Brave instance!")
                self.context = self.browser.contexts[0] if self.browser.contexts else self.browser.new_context()
                self.page = self.context.new_page()
                return
            except Exception as e:
                print(f"[Browser] Could not connect to existing browser on port {debug_port}. Launching a new one.")
            
            # 2. Fallback to launching a new window
            brave_path = os.getenv("BRAVE_PATH", r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe")
            
            if not os.path.exists(brave_path):
                print("[Browser] Brave not found at configured path. Falling back to Chromium.")
                self.browser = self.playwright.chromium.launch(headless=False)
            else:
                self.browser = self.playwright.chromium.launch(headless=False, executable_path=brave_path)
                
            self.context = self.browser.new_context()
            self.page = self.context.new_page()
            print("[Browser] New Browser initialized.")
            
    def close(self):
        """Closes the browser instance."""
        if self.playwright:
            print("[Browser] Closing browser...")
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            self.playwright.stop()
            self.playwright = None

    def get_page(self):
        """Returns the active page, starting the browser if necessary."""
        if not self.page or self.page.is_closed():
            self.start()
        return self.page

# Global singleton to keep the browser alive between commands
_manager = BrowserManager()

def search_google(query: str):
    """Navigates to Google and searches the query."""
    print(f"[Browser Tools] Searching Google for: {query}")
    try:
        page = _manager.get_page()
        page.goto("https://www.google.com")
        
        # Determine the search box selector and type the query
        search_box = page.locator("textarea[name='q'], input[name='q']").first
        search_box.fill(query)
        search_box.press("Enter")
        
        # Wait a moment for results to load
        page.wait_for_load_state("networkidle", timeout=5000)
        return f"Successfully searched Google for {query}."
    except Exception as e:
        print(f"[Browser Error] {e}")
        return "Sorry, I failed to search Google."

def navigate_to(url: str):
    """Navigates the browser to the exact URL provided."""
    print(f"[Browser Tools] Navigating to: {url}")
    if not url.startswith("http"):
        url = "https://" + url
        
    try:
        page = _manager.get_page()
        page.goto(url)
        # Wait a moment for page to load
        page.wait_for_load_state("networkidle", timeout=5000)
        return f"Successfully navigated to {url}."
    except Exception as e:
        print(f"[Browser Error] {e}")
        return f"Sorry, I failed to navigate to {url}."

def search_youtube(query: str):
    """Navigates to YouTube and searches the query."""
    print(f"[Browser Tools] Searching YouTube for: {query}")
    try:
        page = _manager.get_page()
        page.goto("https://www.youtube.com")
        
        # Determine the search box selector and type the query
        # YouTube often uses name="search_query" for its main search input
        search_box = page.locator("input[name='search_query']").first
        
        search_box.wait_for(state="visible", timeout=10000)
        search_box.fill(query)
        search_box.press("Enter")
        
        # Wait a moment for results to load
        page.wait_for_load_state("networkidle", timeout=5000)
        return f"Successfully searched YouTube for {query}."
    except Exception as e:
        print(f"[Browser Error] {e}")
        return "Sorry, I failed to search YouTube."

def cleanup():
    """Called on exit to close the browser."""
    _manager.close()
