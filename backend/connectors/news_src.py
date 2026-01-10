"""GNews API Connector for FlashPoint Intelligence Pipeline

Periodically queries GNews API for global news articles matching a search query.
Deduplicates by URL and normalizes into unified event schema for Pathway.

Features:
- Polling-based collection (configurable interval)
- Built-in deduplication (tracks URLs)
- Graceful error handling (quota limits, network failures)
- Structured event emission into Pathway dataflow
"""

import pathway as pw
import requests
import time

class NewsSource(pw.io.python.ConnectorSubject):
    """
    Pathway-compatible polling connector for news APIs (GNews).

    This source:
    - Periodically queries a news aggregation API
    - Deduplicates articles by URL
    - Normalizes articles into a unified event schema
    - Streams structured updates into the Pathway dataflow
    """
    def __init__(self, api_key, query="crisis OR war OR military", source="gnews", polling_interval=300):
        """
        Initialize the news source connector.

        Args:
            api_key (str): API key for the news provider
            query (str): Search query used to fetch relevant articles
            source (str): Logical source identifier (kept for extensibility)
            polling_interval (int): Interval (seconds) between API polls
        """
        super().__init__()
        self.api_key = api_key
        self.query = query
        self.polling_interval = polling_interval
        # Track URLs of already ingested articles to avoid duplicates
        self.seen_articles = set()

    def run(self):
        """
        Main execution loop.

        Periodically queries the news API for newly published articles
        and emits unseen items into the Pathway pipeline.
        """
        print(f"📡 [GNews] Engine started. Monitoring query: {self.query}")
        
        while True:
            try:
                # ========== API REQUEST CONSTRUCTION ==========
                # Build URL with query params: search terms, language, sort, auth
                url = f"https://gnews.io/api/v4/search?q={self.query}&lang=en&sortby=publishedAt&token={self.api_key}"
                response = requests.get(url, timeout=10)
                
                # ========== SUCCESS RESPONSE HANDLING ==========
                if response.status_code == 200:
                    data = response.json()
                    new_count = 0
                    
                    # Process each article returned by API
                    for article in data.get("articles", []):
                        # Deduplication: skip if URL already seen
                        if article['url'] not in self.seen_articles:
                            
                            # ========== NORMALIZE TO UNIFIED SCHEMA ==========
                            # Extract title + description for content
                            # Extract source, URL, timestamp, and bias tag
                            self.next(
                                text=f"{article['title']}: {article['description']}",
                                source=f"GNews/{article['source']['name']}",
                                url=article['url'],
                                timestamp=time.time(),
                                bias="Western/Global"  # GNews is Western-centric
                            )
                            
                            # Mark URL as seen for deduplication
                            self.seen_articles.add(article['url'])
                            new_count += 1
                    
                    # Log ingestion results
                    if new_count > 0:
                        print(f"📰 [GNews] Ingested {new_count} new articles.")
                        
                # ========== ERROR HANDLING: API QUOTA ==========
                elif response.status_code == 403:
                    print("⚠️ [GNews] Quota Exceeded! Switching to dormant mode.")
                    
                # ========== ERROR HANDLING: OTHER HTTP ERRORS ==========
                else:
                    print(f"❌ [GNews] Error {response.status_code}: {response.text}")

            # ========== NETWORK/TIMEOUT ERROR HANDLING ==========
            except Exception as e:
                print(f"⚠️ [GNews] Connection Error: {e}")

            # Wait before next poll
            time.sleep(self.polling_interval)