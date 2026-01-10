"""RSS Feed Connector for FlashPoint Intelligence Pipeline

Periodically polls RSS feeds from news sources with different geopolitical biases.
Cleans HTML markup from feed content and normalizes into unified event schema.

Features:
- Polling-based RSS collection
- HTML tag removal (img, video, br, etc.)
- Deduplication by article URL
- Support for multiple feed formats
- Bias tagging (Pro-Russia, Pro-China, Western, etc.)
"""

import pathway as pw
import feedparser
import time
from bs4 import BeautifulSoup  # HTML parsing for cleanup

class RssSource(pw.io.python.ConnectorSubject):
    """RSS feed polling connector with HTML cleaning
    
    Attributes:
        url (str): RSS feed URL
        source (str): Source name for event metadata
        bias_tag (str): Geopolitical bias indicator
        polling_interval (int): Seconds between polls
        seen_links (set): Tracks ingested articles by URL
    """
    
    def __init__(self, url, source, bias_tag, polling_interval=300):
        """Initialize RSS source
        
        Args:
            url (str): RSS feed URL
            source (str): Source label (e.g., "Russia Today")
            bias_tag (str): Bias descriptor (e.g., "Pro Russia")
            polling_interval (int): Poll frequency in seconds
        """
        super().__init__()
        self.url = url
        self.source = source
        self.bias_tag = bias_tag
        self.polling_interval = polling_interval
        self.seen_links = set()  # Deduplication tracker

    def _clean_html(self, raw_html):
        """Removes HTML tags and normalizes whitespace
        
        Strategy:
        - Parse HTML with BeautifulSoup
        - Extract text content with space-aware separation
        - Collapse multiple spaces into single space
        - Avoids word merging (e.g., 'end.Start' → 'end Start')
        
        Args:
            raw_html (str): HTML content from feed entry
        
        Returns:
            str: Clean text without tags or excess whitespace
        """
        if not raw_html:
            return ""
        
        # ========== HTML PARSING ==========
        # 1. Parse HTML
        soup = BeautifulSoup(raw_html, "html.parser")
        
        # ========== TEXT EXTRACTION ==========
        # 2. Extract text with a space separator (avoids merging words)
        text = soup.get_text(separator=" ")
        
        # ========== WHITESPACE NORMALIZATION ==========
        # 3. Remove extra whitespace (multiple spaces → single space)
        return " ".join(text.split())

    def run(self):
        """Main polling loop: fetch, parse, clean, and emit RSS entries
        
        Process:
        1. Fetch RSS feed
        2. Iterate through entries
        3. Check deduplication by URL
        4. Clean HTML from title and summary
        5. Normalize to unified schema
        6. Emit to Pathway
        7. Wait for next poll interval
        """
        print(f"📡 [RSS] Engine started. Monitoring: {self.source}")
        
        # ========== MAIN POLLING LOOP ==========
        while True:
            try:
                # Fetch and parse RSS feed
                feed = feedparser.parse(self.url)
                new_count = 0
                
                # ========== PROCESS FEED ENTRIES ==========
                for entry in feed.entries:
                    # Deduplication: skip if URL already seen
                    if entry.link not in self.seen_links:
                        
                        # ========== STEP 1: GET RAW DATA ==========
                        # Extract title and summary/description (fallback behavior)
                        raw_title = entry.get('title', '')
                        raw_summary = entry.get('summary', '') or entry.get('description', '')
                        
                        # ========== STEP 2: CLEAN HTML (The Magic Step) ==========
                        # Remove all HTML markup from both fields
                        clean_title = self._clean_html(raw_title)
                        clean_summary = self._clean_html(raw_summary)
                        
                        # Combine cleaned fields for AI processing
                        full_text = f"{clean_title}: {clean_summary}"
                        
                        # ========== STEP 3: NORMALIZE TO UNIFIED SCHEMA ==========
                        # Send clean data to Pathway
                        self.next(
                            text=full_text,
                            source=self.source,
                            url=entry.link,
                            timestamp=time.time(),
                            bias=self.bias_tag
                        )
                        
                        # Mark URL as seen (deduplication)
                        self.seen_links.add(entry.link)
                        new_count += 1
                
                # Log ingestion results
                if new_count > 0:
                    print(f"🚩 [RSS] {self.source}: Ingested {new_count} clean items.")
                    
            except Exception as e:
                # Handle feed fetch/parse errors
                print(f"⚠️ [RSS] Error fetching {self.url}: {e}")
            
            # ========== POLLING INTERVAL ==========
            time.sleep(self.polling_interval)