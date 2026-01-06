import pathway as pw
import requests
import time
from utils.logger import logger
import feedparser

class NewsSource(pw.io.InputConnector):
    """
    Polls the GNews API for real-time geopolitical updates.
    Falls back to a 'simulation' mode if the API quota is hit.
    """
    
    def __init__(self, api_key, query="crisis OR war OR military", polling_interval=300):
        self.api_key = api_key
        self.query = query
        self.polling_interval = polling_interval  # Seconds between polls
        self.seen_articles = set() # Dedup filter

    def read(self):
        # The main loop that 'yields' data into Pathway
        while True:
            try:
                # 1. Fetch Data
                url = f"https://gnews.io/api/v4/search?q={self.query}&lang=en&sortby=publishedAt&token={self.api_key}"
                response = requests.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    for article in data.get("articles", []):
                        # 2. Filter Duplicates (dedup)
                        # We use URL as a unique ID
                        if article['url'] not in self.seen_articles:
                            
                            # 3. Yield to Pathway Engine
                            yield {
                                "text": f"{article['title']}: {article['description']}",
                                "source": f"GNews/{article['source']['name']}",
                                "url": article['url'],
                                "timestamp": time.time(), # Current ingest time
                                "bias_tag": "Western/Global" # Default tag
                            }
                            
                            self.seen_articles.add(article['url'])
                            
                elif response.status_code == 403:
                    logger.warning("⚠️ GNews API Quota Exceeded")
                    
            except Exception as e:
                logger.error(f"⚠️ Error fetching news: {e}")

            # 4. Wait before next poll to save API credits
            time.sleep(self.poll_interval)



class RssSource(pw.io.InputConnector):
    """
    Reads from RSS feeds to get specific 'Eastern Bloc' narratives
    that might be missing from standard Western APIs.
    """
    def __init__(self, url, bias_tag, polling_interval=250):
        self.url = url
        self.bias_tag = bias_tag  # e.g., "State-Media (RU)"
        self.polling_interval = polling_interval
        self.seen_links = set()

    def read(self):
        while True:
            try:
                feed = feedparser.parse(self.url)
                for entry in feed.entries:
                    if entry.link not in self.seen_links:
                        yield {
                            "text": f"{entry.title}: {entry.summary}",
                            "source": f"{self.bias_tag} / {feed.feed.get('title', 'Unknown')}",
                            "url": entry.link,
                            "timestamp": time.time(),
                            "bias_tag": self.bias_tag
                        }
                        self.seen_links.add(entry.link)
            except Exception as e:
                logger.error(f"⚠️ Error fetching RSS {self.url}: {e}")
            
            time.sleep(self.polling_interval)