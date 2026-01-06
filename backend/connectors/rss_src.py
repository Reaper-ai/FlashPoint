# backend/connectors/rss_source.py
import pathway as pw
import feedparser
import time
from bs4 import BeautifulSoup  # <--- Add this

class RssSource(pw.io.python.ConnectorSubject):
    def __init__(self, url, source, bias_tag, polling_interval=300):
        super().__init__()
        self.url = url
        self.source = source
        self.bias_tag = bias_tag
        self.polling_interval = polling_interval
        self.seen_links = set()

    def _clean_html(self, raw_html):
        """
        Removes HTML tags (<img>, <video>, <br>) and returns clean text.
        """
        if not raw_html:
            return ""
        # 1. Parse HTML
        soup = BeautifulSoup(raw_html, "html.parser")
        
        # 2. Extract text with a space separator (avoids merging words like 'end.Start')
        text = soup.get_text(separator=" ")
        
        # 3. Remove extra whitespace
        return " ".join(text.split())

    def run(self):
        print(f"📡 [RSS] Engine started. Monitoring: {self.source}")
        
        while True:
            try:
                feed = feedparser.parse(self.url)
                new_count = 0
                
                for entry in feed.entries:
                    if entry.link not in self.seen_links:
                        
                        # 1. Get Raw Data
                        raw_title = entry.get('title', '')
                        raw_summary = entry.get('summary', '') or entry.get('description', '')
                        
                        # 2. CLEAN IT (The Magic Step)
                        clean_title = self._clean_html(raw_title)
                        clean_summary = self._clean_html(raw_summary)
                        
                        # Combine them for the AI
                        full_text = f"{clean_title}: {clean_summary}"
                        
                        # 3. Send Clean Data
                        self.next(
                            text=full_text,
                            source=self.source,
                            url=entry.link,
                            timestamp=time.time(),
                            bias=self.bias_tag
                        )
                        
                        self.seen_links.add(entry.link)
                        new_count += 1
                
                if new_count > 0:
                    print(f"🚩 [RSS] {self.source}: Ingested {new_count} clean items.")
                    
            except Exception as e:
                print(f"⚠️ [RSS] Error fetching {self.url}: {e}")
            
            time.sleep(self.polling_interval)