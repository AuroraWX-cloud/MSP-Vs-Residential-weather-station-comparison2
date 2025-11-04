# Modified for GitHub Actions: Single cycle (URL2 immediate -> precise sleep to :03 -> URL1)
# Syncs second screenshot to exact :03:00 UTC to avoid drift.

import time
import os
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from PIL import Image, ImageDraw, ImageFont  # For adding timestamp overlay

# Configuration
URL1 = "https://forecast.weather.gov/MapClick.php?lon=-93.222&lat=44.884"  # weather.gov (at exact :03)
URL2 = "https://www.wunderground.com/wundermap?lat=44.882&lon=-93.222&zoom=12.5"  # Wunderground (immediate)
SCREENSHOT_DIR = "./screenshots"  # Folder for GitHub Actions
SCROLL_AMOUNT = 350  # Pixels to scroll down for URL1

# Create screenshots folder if it doesn't exist
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def add_timestamp_overlay(filepath):
    """
    Adds a timestamp overlay to the screenshot image in the top-left corner.
    """
    try:
        img = Image.open(filepath)
        draw = ImageDraw.Draw(img)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        text = f"Taken: {timestamp}"
        try:
            font = ImageFont.truetype("arial.ttf", 24)
        except:
            font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x, y = 10, 10
        draw.rectangle([x-5, y-5, x + text_width + 5, y + text_height + 5], fill=(255, 255, 255, 128))
        draw.text((x, y), text, fill=(0, 0, 0), font=font)
        img.save(filepath)
        print(f"Timestamp overlay added to: {filepath}")
    except Exception as e:
        print(f"Error adding timestamp overlay to {filepath}: {e}")

def take_screenshot(url, prefix, scroll=0, add_overlay=False):
    """
    Opens the URL in Chrome, optionally scrolls down, takes a full-page screenshot, and saves it.
    Optionally adds a text overlay with the capture time.
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-gpu")  # Extra for Linux (GitHub's Ubuntu)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        driver.get(url)
        time.sleep(8)  # Wait for load
        
        if scroll > 0:
            driver.execute_script(f"window.scrollTo(0, {scroll});")
            time.sleep(1)
        
        # Generate human-readable timestamp for filename (hyphens for compatibility)
        timestamp = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
        filename = f"{prefix} {timestamp}.png"
        filepath = f"{SCREENSHOT_DIR}/{filename}"
        
        driver.save_screenshot(filepath)
        print(f"Screenshot saved: {filepath}")
        
        if add_overlay:
            add_timestamp_overlay(filepath)
        
    except Exception as e:
        print(f"Error taking screenshot of {url}: {e}")
    
    finally:
        driver.quit()

if __name__ == "__main__":
    print("Starting single cycle: URL2 (Wunderground) immediate -> sync sleep to :03 -> URL1 (weather.gov)")
    # Take URL2 first (with overlay)
    take_screenshot(URL2, "Wunderground", add_overlay=True)
    
    # Calculate precise sleep to next :03:00 UTC
    now = datetime.utcnow()  # Use UTC for consistency with cron
    target = now.replace(minute=3, second=0, microsecond=0)
    if now >= target:
        target += timedelta(hours=1)
    wait_seconds = (target - now).total_seconds()
    print(f"Syncing: Sleeping {wait_seconds/60:.1f} minutes to hit exact :03 UTC...")
    time.sleep(wait_seconds)
    
    # Take URL1 (with scroll)
    take_screenshot(URL1, "NWS OBS", scroll=SCROLL_AMOUNT)
    
    print("Cycle complete. Check ./screenshots/ for files.")