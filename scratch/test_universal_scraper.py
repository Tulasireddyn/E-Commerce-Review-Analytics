import os
import sys
import json
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
from dotenv import load_dotenv

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

def fetch_page_text(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US, en;q=0.5',
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.extract()
            
        text = soup.get_text(separator=' ', strip=True)
        # Limit text length to avoid token limits (e.g. first 20000 characters)
        return text[:20000]
    except Exception as e:
        print(f"Error fetching page: {e}")
        return ""

def extract_with_gemini(text):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("No GEMINI_API_KEY")
        return None
        
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = """
    You are an AI trained to extract product data from e-commerce page text.
    Extract the following details from the text below and return ONLY a valid JSON object.
    If a field is not found, use appropriate default values (0 for numbers, empty strings/lists for text).
    
    JSON Schema:
    {
        "title": "Product Title",
        "price": 123.45,
        "features": ["Feature 1", "Feature 2"],
        "rating": 4.5,
        "review_count": 1500,
        "reviews": [
            {"title": "Review Title", "text": "Review text...", "rating": 5.0, "date": "Jan 1, 2023"}
        ]
    }
    
    Text:
    """ + text
    
    try:
        response = model.generate_content(prompt)
        content = response.text
        # Clean up markdown code blocks if any
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
            
        return json.loads(content.strip())
    except Exception as e:
        print(f"Gemini error: {e}")
        return None

if __name__ == "__main__":
    url = "https://www.flipkart.com/xiaomi-x-series-108-cm-43-inch-ultra-hd-4k-led-smart-google-tv-dolby-vision-hdr-10-30w-audio-sound-film-maker-mode-mi/p/itmd84a8d90cae9f?pid=TVSHBPGH65KFAQYQ&lid=LSTTVSHBPGH65KFAQYQ1ZY1OQ&marketplace=FLIPKART&q=tv&store=ckf%2Fczl&spotlightTagId=BestsellerId_ckf%2Fczl&srno=s_1_1&otracker=search&otracker1=search&fm=Search&iid=c413b516-e414-4a47-a8b2-5fba846b0a6d.TVSHBPGH65KFAQYQ.SEARCH&ppt=sp&ppn=sp&ssid=t65q9980s00000001715091216601&qH=c9a1fdac6e082dd8"
    text = fetch_page_text(url)
    if text:
        data = extract_with_gemini(text)
        print(json.dumps(data, indent=2))
    else:
        print("Failed to get text")
