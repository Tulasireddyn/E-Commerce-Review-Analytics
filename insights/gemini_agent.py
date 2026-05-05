import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

def generate_insights(product_data, reviews_df, competitor_data, revenue_data):
    """
    Passes the structured data to Gemini to generate actionable business insights.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "⚠️ **Error:** `GEMINI_API_KEY` is not set in the `.env` file. Please set it to enable AI Insights."
        
    try:
        genai.configure(api_key=api_key)
        # Fallback to gemini-pro if 1.5 is unavailable
        model = genai.GenerativeModel('gemini-1.5-pro') 
        
        # Prepare context
        product_context = f"Product: {product_data.get('title')}\nPrice: ${product_data.get('price')}\nRating: {product_data.get('rating')}\n"
        
        sentiment_summary = ""
        pain_points_context = ""
        
        if reviews_df is not None and not reviews_df.empty:
            sentiments = reviews_df['sentiment'].value_counts().to_dict()
            sentiment_summary = f"Sentiment Breakdown: {sentiments}\n"
            
            # Extract sample negative reviews for pain points
            negatives = reviews_df[reviews_df['sentiment'] == 'Negative']
            if not negatives.empty:
                pain_points_context = "Key complaints/Negative Reviews:\n"
                for idx, row in negatives.head(10).iterrows():
                    pain_points_context += f"- {row['text']}\n"
                    
        revenue_context = f"Estimated Monthly Sales: {revenue_data.get('estimated_monthly_sales')}\nEstimated Monthly Revenue: ${revenue_data.get('estimated_monthly_revenue')}\n"
        
        competitor_context = "Competitors:\n"
        for comp in competitor_data:
            competitor_context += f"- {comp.get('title')} (${comp.get('price')}) - Rating: {comp.get('rating')}\n"
            
        prompt = f"""
        You are an expert Amazon seller consultant. I am providing you with scraped data for an Amazon product, its reviews, and competitors.
        
        {product_context}
        {revenue_context}
        {sentiment_summary}
        {pain_points_context}
        {competitor_context}
        
        Please provide a concise, high-impact business report that tells the seller WHY their product is failing (or succeeding) and HOW to fix it. 
        Focus on:
        1. Key Customer Pain Points (what people hate based on the reviews).
        2. Competitor Advantage (what competitors are doing better based on price/rating).
        3. Actionable Recommendations (how to improve the product or listing).
        
        Format the output in clear, readable Markdown with headings and bullet points. Be direct and insightful.
        """
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"⚠️ **Error generating AI insights:** {str(e)}"
