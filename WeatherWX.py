# Standalone Screenshot Automation App
# Run via .exe built with PyInstaller for Windows 11.
# Takes screenshots of two websites: URL2 (Wunderground) at :53 of each hour, URL1 (weather.gov) 10 min later at :03 of next hour.
# Screenshots are saved to the same directory as this script, with timestamps in the filename.
# URL2 has timestamp overlay; URL1 has scroll down.

import time
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from PIL import Image, ImageDraw, ImageFont  # For adding timestamp overlay

# Configuration
URL1 = "https://forecast.weather.gov/MapClick.php?lon=-93.222&lat=44.884"  # First website: Forecast page (taken at :03)
URL2 = "https://www.wunderground.com/wundermap?lat=44.882&lon=-93.222&zoom=13"  # Second website: WunderMap zoomed to MSP (taken at :53)
SCREENSHOT_DIR = "."  # Saves to app's folder; change to r"C:\Screenshots" for fixed path
SCROLL_AMOUNT = 300  # Pixels to scroll down for URL1


def add_timestamp_overlay(filepath):
    """
    Adds a timestamp overlay to the screenshot image in the top-left corner.
    """
    try:
        # Open the image
        img = Image.open(filepath)
        draw = ImageDraw.Draw(img)

        # Get current timestamp (human-readable)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        text = f"Taken: {timestamp}"

        # Use a default font (size 24; adjust as needed)
        try:
            font = ImageFont.truetype("arial.ttf", 24)  # Assumes Arial on Windows
        except:
            font = ImageFont.load_default()  # Fallback

        # Calculate text position (top-left with padding)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = 10
        y = 10

        # Draw semi-transparent background for readability (white with alpha)
        draw.rectangle([x - 5, y - 5, x + text_width + 5, y + text_height + 5], fill=(255, 255, 255, 128))

        # Draw the text (black)
        draw.text((x, y), text, fill=(0, 0, 0), font=font)

        # Save the modified image (overwrite original)
        img.save(filepath)
        print(f"Timestamp overlay added to: {filepath}")

    except Exception as e:
        print(f"Error adding timestamp overlay to {filepath}: {e}")


def take_screenshot(url, prefix, scroll=0, add_overlay=False):
    """
    Opens the URL in Chrome, optionally scrolls down, takes a full-page screenshot, and saves it.
    Optionally adds a text overlay with the capture time.
    """
    # Set up Chrome options for headless mode
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")

    # Initialize the driver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        driver.get(url)
        time.sleep(8)  # Wait for load

        # Optional scroll down (for URL1)
        if scroll > 0:
            driver.execute_script(f"window.scrollTo(0, {scroll});")
            time.sleep(1)

        # Generate timestamp for filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_{timestamp}.png"
        filepath = f"{SCREENSHOT_DIR}/{filename}"

        # Take screenshot
        driver.save_screenshot(filepath)
        print(f"Screenshot saved: {filepath}")

        # Optional: Add timestamp overlay (for URL2)
        if add_overlay:
            add_timestamp_overlay(filepath)

    except Exception as e:
        print(f"Error taking screenshot of {url}: {e}")

    finally:
        driver.quit()


def main():
    print("Starting screenshot automation. Press Ctrl+C to stop (or end task in Task Manager).")
    print(f"URL2 (Wunderground): Captured at :53 of each hour (with timestamp overlay)")
    print(f"URL1 (weather.gov): Captured 10 min later at :03 (with scroll down {SCROLL_AMOUNT}px)")
    print("Will sync to next :53 for first capture.")

    while True:
        try:
            # Calculate wait time until next :53 for URL2
            now = datetime.now()
            target2 = now.replace(minute=53, second=0, microsecond=0)
            if now > target2:
                target2 += timedelta(hours=1)
            wait_to_url2 = (target2 - now).total_seconds()

            if wait_to_url2 > 0:
                print(f"Waiting {wait_to_url2 / 60:.1f} minutes until {target2.strftime('%H:%M:%S')} for URL2...")
                time.sleep(wait_to_url2)

            # Take URL2 at ~:53
            print(f"Taking URL2 at {datetime.now().strftime('%H:%M:%S')}")
            take_screenshot(URL2, "screenshot2", add_overlay=True)

            # Wait exactly 10 minutes for URL1
            print("Waiting 10 minutes for URL1...")
            time.sleep(600)

            # Take URL1 at ~:03
            print(f"Taking URL1 at {datetime.now().strftime('%H:%M:%S')}")
            take_screenshot(URL1, "screenshot1", scroll=SCROLL_AMOUNT)

            # Loop will now wait until next :53 (from :03, that's ~50 min, but calculated precisely)

        except KeyboardInterrupt:
            print("\nStopped by user.")
            break
        except Exception as e:
            print(f"Unexpected error: {e}")
            time.sleep(60)


if __name__ == "__main__":
    main()