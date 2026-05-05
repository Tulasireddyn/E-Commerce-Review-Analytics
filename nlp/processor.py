from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
import pandas as pd
import numpy as np

# Initialize VADER
analyzer = SentimentIntensityAnalyzer()
# Lazily load the sentence transformer model
embedder = None

def analyze_sentiment(reviews_list):
    """
    Takes a list of review dicts, adds sentiment, and returns a DataFrame.
    """
    if not reviews_list:
        return pd.DataFrame()
        
    df = pd.DataFrame(reviews_list)
    
    def get_sentiment(text):
        scores = analyzer.polarity_scores(str(text))
        compound = scores['compound']
        if compound >= 0.05:
            return 'Positive'
        elif compound <= -0.05:
            return 'Negative'
        else:
            return 'Neutral'
            
    df['sentiment'] = df['text'].apply(get_sentiment)
    df['sentiment_score'] = df['text'].apply(lambda x: analyzer.polarity_scores(str(x))['compound'])
    return df

def extract_topics(df, num_clusters=3):
    """
    Clusters reviews based on text embeddings.
    """
    global embedder
    if df.empty:
        return df
        
    # If we have very few reviews, adjust clusters
    n_clusters = min(num_clusters, len(df))
    if n_clusters <= 1:
        df['topic_cluster'] = 0
        return df
        
    if embedder is None:
        print("Loading sentence-transformers model...")
        embedder = SentenceTransformer('all-MiniLM-L6-v2')
        
    texts = df['text'].tolist()
    print("Encoding texts...")
    embeddings = embedder.encode(texts)
    
    print(f"Clustering into {n_clusters} topics...")
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    kmeans.fit(embeddings)
    
    df['topic_cluster'] = kmeans.labels_
    return df

def get_sentiment_summary(df):
    if df.empty:
        return {}
    summary = df['sentiment'].value_counts().to_dict()
    # Ensure all keys exist
    for k in ['Positive', 'Negative', 'Neutral']:
        if k not in summary:
            summary[k] = 0
    return summary
