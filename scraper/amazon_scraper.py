import requests
from bs4 import BeautifulSoup
import re
import time
import random
import os
from apify_client import ApifyClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15',
]

def get_headers():
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept-Language': 'en-US, en;q=0.5',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Referer': 'https://www.google.com/',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }

def fetch_page(url, retries=3):
    for i in range(retries):
        try:
            response = requests.get(url, headers=get_headers(), timeout=10)
            if response.status_code == 200:
                # Check for captcha
                if "To discuss automated access to Amazon data please contact" in response.text:
                    print("Blocked by Amazon CAPTCHA.")
                    return None
                return BeautifulSoup(response.content, 'html.parser')
            elif response.status_code == 404:
                print(f"Page not found: {url}")
                return None
            else:
                print(f"Failed to fetch page. Status: {response.status_code}")
        except Exception as e:
            print(f"Error fetching {url}: {e}")
        time.sleep(random.uniform(2, 5))
    return None

def extract_product_details(soup):
    details = {
        'title': 'Unknown Title',
        'price': 0.0,
        'features': [],
        'rating': 0.0,
        'review_count': 0
    }
    
    if not soup:
        return details
        
    # Title
    title_element = soup.find('span', {'id': 'productTitle'})
    if title_element:
        details['title'] = title_element.text.strip()
        
    # Price
    price_element = soup.find('span', {'class': 'a-price-whole'})
    price_fraction = soup.find('span', {'class': 'a-price-fraction'})
    if price_element:
        price_str = price_element.text.strip().replace(',', '')
        if price_fraction:
            price_str += price_fraction.text.strip()
        try:
            details['price'] = float(re.search(r'\d+\.?\d*', price_str).group())
        except:
            pass
            
    # Rating
    rating_element = soup.find('span', {'data-hook': 'rating-out-of-text'}) or soup.find('i', {'class': 'a-icon-star'})
    if rating_element:
        try:
            details['rating'] = float(rating_element.text.split(' ')[0])
        except:
            pass
            
    # Review Count
    review_count_element = soup.find('span', {'id': 'acrCustomerReviewText'})
    if review_count_element:
        try:
            details['review_count'] = int(re.sub(r'[^\d]', '', review_count_element.text))
        except:
            pass

    # Features
    feature_bullets = soup.find('div', {'id': 'feature-bullets'})
    if feature_bullets:
        for li in feature_bullets.find_all('li'):
            text = li.text.strip()
            if text and not "Make sure this fits" in text:
                details['features'].append(text)
                
    return details

def extract_reviews(soup, limit=10):
    reviews = []
    if not soup:
        return reviews
        
    review_elements = soup.find_all('div', {'data-hook': 'review'})
    for el in review_elements[:limit]:
        title = el.find('a', {'data-hook': 'review-title'})
        body = el.find('span', {'data-hook': 'review-body'})
        rating_el = el.find('i', {'data-hook': 'review-star-rating'})
        date_el = el.find('span', {'data-hook': 'review-date'})
        
        if body:
            review_text = body.text.strip()
            review_text = re.sub(r'\n+', ' ', review_text)
            rating = 0
            if rating_el:
                try:
                    rating = float(rating_el.text.split(' ')[0])
                except:
                    pass
            reviews.append({
                'title': title.text.strip() if title else '',
                'text': review_text,
                'rating': rating,
                'date': date_el.text.strip() if date_el else ''
            })
            
    return reviews

def scrape_with_apify(url):
    apify_token = os.getenv("APIFY_API_TOKEN")
    if not apify_token:
        print("APIFY_API_TOKEN not found in environment variables.")
        return None
        
    print(f"Attempting to scrape using Apify API: {url}")
    client = ApifyClient(apify_token)
    
    # We will use the popular "junglee/amazon-crawler" as a default.
    # Users can change this actor ID if they prefer another one.
    run_input = {
        "categoryOrProductUrls": [{"url": url}],
        "maxReviews": 20,
    }
    
    try:
        run = client.actor("junglee/amazon-crawler").call(run_input=run_input)
        
        if run and run.get("defaultDatasetId"):
            dataset_id = run["defaultDatasetId"]
            items = list(client.dataset(dataset_id).iterate_items())
            
            if not items:
                print("Apify run finished but no items were returned.")
                return None
                
            # The structure of items varies by Actor, trying to map typical fields
            item = items[0]
            
            # Map product details
            product = {
                'title': item.get('title', 'Unknown Title'),
                'price': item.get('price', 0.0),
                'features': item.get('bullets', []) or item.get('features', []),
                'rating': item.get('stars', item.get('rating', 0.0)),
                'review_count': item.get('reviewsCount', item.get('reviewCount', 0))
            }
            
            # Map reviews
            reviews = []
            raw_reviews = item.get('reviews', [])
            for rev in raw_reviews:
                reviews.append({
                    'title': rev.get('title', ''),
                    'text': rev.get('text', rev.get('reviewText', '')),
                    'rating': rev.get('stars', rev.get('rating', 0)),
                    'date': rev.get('date', '')
                })
            
            return {
                'status': 'success',
                'product': product,
                'reviews': reviews,
                'competitors': [] # We'd need a separate search scrape for competitors, returning empty for now
            }
    except Exception as e:
        print(f"Error calling Apify API: {e}")
        
    return None

def scrape_amazon_data(url):
    """
    Main entry point for scraping.
    Prioritizes Apify API if token is provided.
    Falls back to local requests scraping, and finally mock data if both fail.
    """
    # 1. Try Apify API
    if os.getenv("APIFY_API_TOKEN"):
        apify_data = scrape_with_apify(url)
        if apify_data:
            return apify_data
    
    # 2. Try Local Scraping
    print(f"Attempting local scrape: {url}")
    soup = fetch_page(url)
    if soup:
        details = extract_product_details(soup)
        reviews = extract_reviews(soup, limit=10)
        
        if details['title'] != 'Unknown Title' and reviews:
            return {
                'status': 'success',
                'product': details,
                'reviews': reviews,
                'competitors': [] 
            }
            
    # 3. Fallback to Mock Data
    print("Scraping failed or blocked. Using fallback mock data for demonstration.")
    return get_mock_data()

def get_mock_data():
    return {
        'status': 'mock',
        'product': {
            'title': 'Anker Soundcore Life Q30 Active Noise Cancelling Headphones',
            'price': 79.99,
            'features': ['Hi-Res Certified Music', 'Multiple Noise Cancellation Modes', '40-Hour Playtime'],
            'rating': 4.5,
            'review_count': 45210
        },
        'reviews': [
            {'text': 'Great sound quality for the price, but the plastic build feels a bit cheap. Noise cancelling is decent, battery lasts forever.', 'rating': 4.0},
            {'text': 'The battery died completely after 3 months. Very disappointed.', 'rating': 1.0},
            {'text': 'Absolutely love these. Better than my old Sonys. The bass is punchy.', 'rating': 5.0},
            {'text': 'Comfortable for long sessions, but the microphone is terrible for calls. People can never hear me clearly.', 'rating': 3.0},
            {'text': 'Best value headphones on the market. ANC works well on airplanes.', 'rating': 5.0},
            {'text': 'Too tight on my head. Causes headaches after an hour of use.', 'rating': 2.0},
            {'text': 'Amazing battery life! I charge them maybe once a week.', 'rating': 5.0},
            {'text': 'Left ear cup stopped working randomly.', 'rating': 1.0},
            {'text': 'They look good and sound great. The app is also very useful for EQ settings.', 'rating': 4.0},
            {'text': 'Price dropped by $20 the day after I bought them. Annoying, but the product is fine.', 'rating': 4.0},
        ],
        'competitors': [
            {'title': 'Sony WH-CH720N Noise Canceling Wireless Headphones', 'price': 98.00, 'rating': 4.4, 'review_count': 12000},
            {'title': 'JBL Tune 760NC - Lightweight, Foldable Wireless Headphones', 'price': 64.95, 'rating': 4.3, 'review_count': 18500},
            {'title': 'Bose QuietComfort 45 Bluetooth Wireless', 'price': 279.00, 'rating': 4.6, 'review_count': 30000},
            {'title': 'Sennheiser HD 450BT Bluetooth 5.0 Wireless Headphone', 'price': 119.95, 'rating': 4.2, 'review_count': 15000},
        ]
    }

