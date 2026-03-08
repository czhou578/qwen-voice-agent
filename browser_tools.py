from playwright.sync_api import sync_playwright

class BrowserManager:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
    
    def start(self):
        """Initializes the browser instance."""
        if not self.playwright:
            self.playwright = sync_playwright().start()
            # Run non-headless so you can see the browser
            self.browser = self.playwright.chromium.launch(headless=False)
            self.context = self.browser.new_context()
            self.page = self.context.new_page()
            print("[Browser] Browser initialized.")
            
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

def cleanup():
    """Called on exit to close the browser."""
    _manager.close()
