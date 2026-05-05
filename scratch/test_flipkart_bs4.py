import requests
from bs4 import BeautifulSoup
import re

url = "https://www.flipkart.com/xiaomi-x-series-108-cm-43-inch-ultra-hd-4k-led-smart-google-tv-dolby-vision-hdr-10-30w-audio-sound-film-maker-mode-mi/p/itmd84a8d90cae9f?pid=TVSHBPGH65KFAQYQ"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US, en;q=0.5',
}

response = requests.get(url, headers=headers)
print(f"Status Code: {response.status_code}")
soup = BeautifulSoup(response.content, 'html.parser')

title_el = soup.find('span', {'class': 'VU-ZEz'})
title = title_el.text if title_el else "Not found"
print(f"Title: {title}")

price_el = soup.find('div', {'class': 'Nx9bqj CxhGGd'})
price = price_el.text if price_el else "Not found"
print(f"Price: {price}")

rating_el = soup.find('div', {'class': 'XQDdHH'})
rating = rating_el.text if rating_el else "Not found"
print(f"Rating: {rating}")
