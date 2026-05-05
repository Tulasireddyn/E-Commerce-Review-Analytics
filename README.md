# 🛒 Universal E-Commerce Analytics

An AI-powered dashboard that automatically scrapes, extracts, and analyzes product data from **any** e-commerce platform (Flipkart, Amazon, Walmart, etc.). Built with Streamlit, Apify, and Google's Gemini 1.5 Pro.

## ✨ Features
* **Universal Scraping:** Paste a product URL from almost any major shopping platform. The system uses Apify to securely bypass basic anti-bot protections and extract raw website text.
* **Intelligent Data Extraction:** The raw HTML/text is passed to a Gemini LLM which dynamically parses and structures the product title, price, features, rating, and customer reviews into strict JSON.
* **Sentiment & NLP Analytics:** Automatically analyzes the sentiment of the extracted reviews to determine overall customer satisfaction.
* **AI Business Insights:** Generates a comprehensive, consultative business report highlighting the primary pain points, advantages over competitors, and actionable recommendations.
* **Mock Data Fallback:** If the scrapers are blocked or API keys are missing, the UI gracefully degrades to a mock dataset for demonstration purposes.

## 🛠️ Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Tulasireddyn/E-Commerce-Review-Analytics.git
   cd E-Commerce-Review-Analytics
   ```

2. **Create a Virtual Environment:**
   ```bash
   python -m venv venv
   
   # Windows:
   .\venv\Scripts\activate
   
   # Mac/Linux:
   source venv/bin/activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables:**
   Create a `.env` file in the root directory and add your API keys. (Do NOT commit this file to GitHub!)
   ```env
   GEMINI_API_KEY="your_gemini_api_key"
   APIFY_API_TOKEN="your_apify_api_token"
   ```

## 🚀 Running the App
Once everything is configured, start the Streamlit dashboard:
```bash
streamlit run app.py
```
This will open the dashboard in your default web browser (usually at `http://localhost:8501`). Simply paste an e-commerce product URL into the text box and click "Analyze Product" to begin.

## 📁 Architecture
- **`app.py`**: The main Streamlit dashboard UI and orchestration layer.
- **`scraper/universal_scraper.py`**: Handles robust text extraction using Apify's `website-content-crawler` (or local requests fallback) and structures it using the `gemini-1.5-pro` model.
- **`insights/gemini_agent.py`**: Feeds the structured data back into Gemini to generate actionable business insights and summaries.
- **`nlp/processor.py`**: Performs traditional Natural Language Processing (NLP) for sentiment analysis and clustering on the extracted reviews.
- **`nlp/revenue.py`**: Contains heuristics to estimate monthly revenue based on review velocity.

## ⚠️ Disclaimer
Web scraping is subject to the Terms of Service of individual platforms. This tool is built for educational and personal analytics purposes. Ensure your use of Apify and automated crawlers complies with the target website's rules.
