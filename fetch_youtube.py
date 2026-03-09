import sys
from playwright.sync_api import sync_playwright
import urllib.parse

def fetch_first_youtube_result(query):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
            page.goto(url)
            page.wait_for_selector("ytd-video-renderer a#thumbnail", timeout=10000)
            href = page.locator("ytd-video-renderer a#thumbnail").first.get_attribute("href")
            browser.close()
            
            if href:
                print(f"SUCCESS:https://www.youtube.com{href}")
            else:
                print("ERROR:NO_HREF")
    except Exception as e:
        print(f"ERROR:{e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        fetch_first_youtube_result(sys.argv[1])
    else:
        print("ERROR:NO_QUERY")
