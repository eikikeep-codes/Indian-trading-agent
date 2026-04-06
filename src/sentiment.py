from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from GoogleNews import GoogleNews
import time

analyzer = SentimentIntensityAnalyzer()

def fetch_sentiment_for_ticker(ticker: str) -> dict:
    """
    Fetches recent news for a ticker and computes VADER sentiment.
    
    Args:
        ticker: The stock ticker (e.g. 'RELIANCE.NS')
        
    Returns:
        Dictionary with score, label, and list of headlines.
    """
    # Clean ticker for searching (e.g. RELIANCE.NS -> RELIANCE NSE)
    search_query = ticker.replace(".NS", " NSE").replace(".BO", " BSE")
    search_query += " stock"
    
    try:
        # GoogleNews configuration: last 7 days, english
        googlenews = GoogleNews(lang='en', period='7d')
        googlenews.get_news(search_query)
        # Avoid hanging if a lot of pages
        results = googlenews.results(sort=True)
    except Exception as e:
        print(f"Error fetching news for {ticker}: {e}")
        return {"score": 0, "label": "Neutral", "headlines": []}

    if not results:
        return {"score": 0, "label": "Neutral", "headlines": []}
        
    headlines = []
    total_compound = 0
    valid_articles = 0
    
    # We'll take the top 5-10 articles
    limit = min(10, len(results))
    for i in range(limit):
        try:
            title = results[i].get('title', '')
            if not title:
                continue
                
            headlines.append(title)
            sentiment_dict = analyzer.polarity_scores(title)
            total_compound += sentiment_dict['compound']
            valid_articles += 1
        except Exception:
            pass

    if valid_articles == 0:
        return {"score": 0, "label": "Neutral", "headlines": []}
        
    avg_score = total_compound / valid_articles
    
    if avg_score >= 0.15:
        label = "Positive"
    elif avg_score <= -0.15:
        label = "Negative"
    else:
        label = "Neutral"
        
    return {
        "score": avg_score, # Range -1 to +1
        "label": label,
        "headlines": headlines
    }
