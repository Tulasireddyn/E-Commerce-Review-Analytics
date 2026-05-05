import streamlit as st
import pandas as pd
import plotly.express as px
from scraper.universal_scraper import scrape_product_data
from nlp.processor import analyze_sentiment, extract_topics, get_sentiment_summary
from nlp.revenue import estimate_revenue
from insights.gemini_agent import generate_insights

st.set_page_config(page_title="Amazon Analytics Dashboard", layout="wide", page_icon="🛒")

# Custom CSS for aesthetics
st.markdown("""
<style>
    .reportview-container .main .block-container{
        max-width: 1200px;
        padding-top: 2rem;
        padding-right: 2rem;
        padding-left: 2rem;
        padding-bottom: 2rem;
    }
    .metric-card {
        background-color: #1E1E1E;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
</style>
""", unsafe_allow_html=True)

st.title("🛒 Universal E-Commerce Analytics")
st.markdown("Enter **any** e-commerce product URL (Amazon, Flipkart, etc.) to generate sentiment breakdown, pain points, competitor comparison, and AI insights. *Note: If blocked, mock data will be used to demonstrate functionality.*")

url_input = st.text_input("Product URL", placeholder="https://www.flipkart.com/...")

if st.button("Analyze Product", type="primary"):
    if url_input:
        with st.spinner("Scraping & Extracting Data with AI (this may take up to 60 seconds)..."):
            scraped_data = scrape_product_data(url_input)
            
        if scraped_data.get('status') == 'mock':
            st.warning("⚠️ Scraper was blocked or failed. Using fallback mock data for demonstration.")
        else:
            st.success("✅ Data scraped successfully!")
            
        product = scraped_data['product']
        reviews = scraped_data['reviews']
        competitors = scraped_data['competitors']
        
        # Header Metrics
        st.header(f"📦 {product['title']}")
        col1, col2, col3, col4 = st.columns(4)
        
        with st.spinner("Estimating Revenue..."):
            revenue_data = estimate_revenue(product)
            
        col1.metric("Price", f"${product['price']}")
        col2.metric("Rating", f"{product['rating']} ⭐")
        col3.metric("Reviews", f"{product['review_count']:,}")
        col4.metric("Est. Monthly Rev", f"${revenue_data['estimated_monthly_revenue']:,}", help="Based on recent review velocity heuristcs")
            
        st.divider()
        
        # NLP Processing
        with st.spinner("Processing NLP (Sentiment & Topics)..."):
            reviews_df = analyze_sentiment(reviews)
            # Extracted topics (clustering)
            reviews_df = extract_topics(reviews_df)
        
        # Row 2: Sentiment and Competitors
        st.subheader("📊 Sentiment & Competitor Breakdown")
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            if not reviews_df.empty:
                sentiment_counts = get_sentiment_summary(reviews_df)
                fig_sentiment = px.pie(
                    names=list(sentiment_counts.keys()), 
                    values=list(sentiment_counts.values()), 
                    title="Review Sentiment Breakdown",
                    color=list(sentiment_counts.keys()),
                    color_discrete_map={'Positive':'#00CC96', 'Negative':'#EF553B', 'Neutral':'#636EFA'}
                )
                fig_sentiment.update_layout(margin=dict(t=40, b=0, l=0, r=0))
                st.plotly_chart(fig_sentiment, use_container_width=True)
            else:
                st.info("No reviews found for sentiment analysis.")
                
        with col_chart2:
            if competitors:
                comp_df = pd.DataFrame(competitors)
                # Add main product to compare
                main_prod = {'title': 'Main Product (You)', 'price': product['price'], 'rating': product['rating']}
                comp_df = pd.concat([pd.DataFrame([main_prod]), comp_df], ignore_index=True)
                
                # Assign colors
                comp_df['Color'] = ['Main Product'] + ['Competitor'] * (len(comp_df) - 1)
                
                fig_comp = px.scatter(
                    comp_df, x="price", y="rating", 
                    text="title", 
                    title="Competitor Comparison (Price vs Rating)",
                    color="Color",
                    color_discrete_map={'Main Product': '#FF9900', 'Competitor': '#232F3E'}
                )
                fig_comp.update_traces(textposition='top center', marker=dict(size=12))
                fig_comp.update_layout(showlegend=False, margin=dict(t=40, b=0, l=0, r=0))
                st.plotly_chart(fig_comp, use_container_width=True)
            else:
                st.info("No competitor data available.")
                
        st.divider()
        
        # Row 3: AI Insights
        st.subheader("🧠 AI-Generated Insights (Gemini 1.5 Pro)")
        with st.spinner("Generating actionable insights..."):
            insights_md = generate_insights(product, reviews_df, competitors, revenue_data)
            st.markdown(insights_md)
            
    else:
        st.error("Please enter a valid product URL.")
