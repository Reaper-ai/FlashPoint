import pathway as pw
import requests
import time

class NewsSource(pw.io.python.ConnectorSubject):
    def __init__(self, api_key, query="crisis OR war OR military", source="gnews", polling_interval=300):
        super().__init__()
        self.api_key = api_key
        self.query = query
        self.polling_interval = polling_interval
        self.seen_articles = set()

    def run(self):
        print(f"📡 [GNews] Engine started. Monitoring query: {self.query}")
        
        while True:
            try:
                url = f"https://gnews.io/api/v4/search?q={self.query}&lang=en&sortby=publishedAt&token={self.api_key}"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    new_count = 0
                    
                    for article in data.get("articles", []):
                        if article['url'] not in self.seen_articles:
                            
                            # PUSH data to Pathway using self.next()
                            self.next(
                                text=f"{article['title']}: {article['description']}",
                                source=f"GNews/{article['source']['name']}",
                                url=article['url'],
                                timestamp=time.time(),
                                bias="Western/Global"
                            )
                            
                            self.seen_articles.add(article['url'])
                            new_count += 1
                    
                    if new_count > 0:
                        print(f"📰 [GNews] Ingested {new_count} new articles.")
                        
                elif response.status_code == 403:
                    print("⚠️ [GNews] Quota Exceeded! Switching to dormant mode.")
                else:
                    print(f"❌ [GNews] Error {response.status_code}: {response.text}")

            except Exception as e:
                print(f"⚠️ [GNews] Connection Error: {e}")

            time.sleep(self.polling_interval)