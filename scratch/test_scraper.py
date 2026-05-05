import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scraper.universal_scraper import scrape_product_data

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

url = "https://www.flipkart.com/xiaomi-x-series-108-cm-43-inch-ultra-hd-4k-led-smart-google-tv-dolby-vision-hdr-10-30w-audio-sound-film-maker-mode-mi/p/itmd84a8d90cae9f?pid=TVSHBPGH65KFAQYQ"
print("Testing scrape...")
result = scrape_product_data(url)
print(result)
