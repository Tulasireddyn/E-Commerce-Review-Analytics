import os
import json
import re
import requests
from bs4 import BeautifulSoup
from apify_client import ApifyClient
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def fetch_page_text_local(url):
    """Fallback method: Extracts visible text using local requests."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0',
        'Accept-Language': 'en-US, en;q=0.5',
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove noisy elements
        for script in soup(["script", "style", "nav", "footer", "header", "noscript"]):
            script.extract()
            
        text = soup.get_text(separator=' ', strip=True)
        # Limit to avoid token explosion (Gemini 1.5 Pro has 1M context, but let's be safe)
        return text[:40000]
    except Exception as e:
        print(f"Local fetch error: {e}")
        return ""

def fetch_page_text_apify(url):
    """Primary method: Uses Apify to extract text robustly."""
    apify_token = os.getenv("APIFY_API_TOKEN")
    if not apify_token:
        print("APIFY_API_TOKEN not found, falling back to local scraping.")
        return None
        
    print(f"Scraping {url} via Apify...")
    client = ApifyClient(apify_token)
    
    # website-content-crawler extracts clean markdown text
    run_input = {
        "startUrls": [{"url": url}],
        "maxCrawlPages": 1,
        "crawlerType": "playwright:adaptive",
        "dynamicContentWaitSecs": 5,
    }
    
    try:
        run = client.actor("apify/website-content-crawler").call(run_input=run_input)
        if run and run.get("defaultDatasetId"):
            dataset_id = run["defaultDatasetId"]
            items = list(client.dataset(dataset_id).iterate_items())
            if items:
                return items[0].get("markdown", items[0].get("text", ""))
    except Exception as e:
        print(f"Apify error: {e}")
    return None

def extract_structured_data_with_gemini(text):
    """Uses Gemini 1.5 Pro to extract structured JSON from raw page text."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY is not set.")
        return None
        
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        prompt = """
        You are a highly capable data extraction AI. Read the following raw website text from an e-commerce product page.
        Extract the product details and reviews into a strict JSON format. 
        If certain fields are completely missing, use 0 for numbers and empty lists for lists.
        Do NOT wrap the output in markdown codeblocks like ```json, just return the raw JSON string.

        Expected JSON format:
        {
            "product": {
                "title": "Full product title",
                "price": 123.45,
                "features": ["Feature 1", "Feature 2"],
                "rating": 4.5,
                "review_count": 120
            },
            "reviews": [
                {
                    "title": "Review title",
                    "text": "Full review text...",
                    "rating": 5.0,
                    "date": "Review date"
                }
            ],
            "competitors": []
        }

        Website Text (excerpt):
        """ + text[:40000] # Ensure we don't send too much if the page is insane
        
        response = model.generate_content(prompt)
        content = response.text.strip()
        
        # Cleanup potential markdown wrapping just in case
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
            
        data = json.loads(content.strip())
        return data
    except Exception as e:
        print(f"Gemini Extraction Error: {e}")
        return None

def get_universal_mock_data():
    return {
        'status': 'mock',
        'product': {
            'title': 'Universal AI Headphones (Mock Data Fallback)',
            'price': 199.99,
            'features': ['Noise Cancelling', 'Wireless', '40hr Battery'],
            'rating': 4.7,
            'review_count': 500
        },
        'reviews': [
            {'title': 'Great', 'text': 'I love these headphones!', 'rating': 5.0, 'date': '2023-01-01'},
            {'title': 'Okay', 'text': 'A bit expensive for what you get.', 'rating': 3.0, 'date': '2023-01-02'}
        ],
        'competitors': []
    }

def scrape_product_data(url):
    """
    Main entry point for universal scraping.
    1. Try Apify to get text.
    2. Fallback to Local Requests to get text.
    3. Use Gemini to extract JSON.
    4. Fallback to mock data if all fails.
    """
    print(f"Starting Universal Scrape for: {url}")
    
    text = fetch_page_text_apify(url)
    if not text:
        text = fetch_page_text_local(url)
        
    if text:
        print(f"Extracted {len(text)} characters of text. Sending to Gemini...")
        structured_data = extract_structured_data_with_gemini(text)
        if structured_data and 'product' in structured_data:
            structured_data['status'] = 'success'
            return structured_data
            
    print("Scraping failed or AI extraction failed. Using fallback mock data.")
    return get_universal_mock_data()
