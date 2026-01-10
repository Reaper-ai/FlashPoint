"""Reddit Public API Connector for FlashPoint Intelligence Pipeline

Polls Reddit's public JSON API for recent posts from monitored subreddits.
Uses multi-subreddit syntax to aggregate discussions across relevant communities.

Features:
- Polling-based collection with rate limit handling (429 backoff)
- Deduplication by post ID
- Light text processing (combines title + body)
- Handles both text posts and link posts
- Graceful memory management (deduplication set reset)
"""

import time
import requests
import pathway as pw 


# ========== COLLECTION PARAMETERS ==========
# Subreddits monitored (combined using Reddit's multi-subreddit syntax)
SUBREDDITS = "worldnews+geopolitics+technology+artificialintelligence"
# Number of newest posts fetched per poll
SUBREDDITS = "worldnews+geopolitics+news"
POST_LIMIT = 50
# Polling interval in seconds (kept conservative to avoid rate limits)
POLL_INTERVAL = 60  # Seconds (Safe rate limit)

class RedditSource(pw.io.python.ConnectorSubject):
    """
    Pathway-compatible polling connector for Reddit.

    This source:
    - Polls Reddit's public JSON API
    - Performs lightweight deduplication
    - Normalizes posts into a unified event format
    - Streams results directly into the Pathway pipeline
    """
    def run(self):
        """
        Main execution loop.

        Continuously polls Reddit for new posts and pushes unseen content
        into the Pathway dataflow.
        """
        # ========== INITIALIZATION ==========
        seen_ids = set()  # Track ingested post IDs
        # Reddit endpoint for newest posts across selected subreddits
        url = f"https://www.reddit.com/r/{SUBREDDITS}/new.json?limit={POST_LIMIT}"
        # Custom User-Agent required by Reddit API rules
        headers = {
            'User-Agent': 'FlashPointEngine/1.0 (Macintosh; Intel Mac OS X 10_15_7)'
        }
        print(f"📡 [Reddit] Engine started. Monitoring: r/{SUBREDDITS}")
        
        # ========== MAIN POLLING LOOP ==========
        while True:
            try:
                response = requests.get(url, headers=headers, timeout=10)
                
                # ========== RATE LIMIT HANDLING ==========
                # HTTP 429 indicates too many requests
                if response.status_code == 429:
                    print("⚠️ [Reddit] Rate Limited! Cooling down for 2 minutes...")
                    time.sleep(120)  # Back off before retry
                    continue
                
                # ========== SUCCESSFUL RESPONSE ==========
                if response.status_code == 200:
                    data = response.json()
                    posts = data.get('data', {}).get('children', [])
                    new_count = 0

                    # ========== PROCESS POSTS ==========
                    # Process newest posts first
                    for item in posts:
                        post = item.get('data', {})
                        post_id = post.get('id')

                        # Deduplication: process only unseen posts
                        if post_id not in seen_ids:
                            seen_ids.add(post_id)
                            new_count += 1

                            # ========== EXTRACT TEXT CONTENT ==========
                            # Get title (always present)
                            title = post.get('title', '').strip()
                            # Check if it's a text post (not a link post)
                            is_text_post = post.get('is_self', False)
                            # Extract body for text posts, empty for links
                            body = post.get('selftext', '').strip() if is_text_post else ""

                            # Combine title and body for AI processing
                            full_text = f"{title}\n{body}"

                            # ========== NORMALIZE TO UNIFIED SCHEMA ==========
                            # Build event record with all metadata
                            row = {
                                "source": "Reddit",
                                "text": full_text,
                                "url": f"https://reddit.com{post.get('permalink')}",
                                "timestamp": float(post.get('created_utc', 0)),
                                "bias": "Varied/Unknown"  # Reddit posts have mixed bias
                            }
                            # Emit event into Pathway engine
                            self.next(**row)
                            print(f"👾 [Reddit] {title[:40]}...", flush=True)
                            
                        # ========== MEMORY MANAGEMENT ==========
                        # Prevent unbounded memory growth of dedup set
                        if len(seen_ids) > 5000:
                            seen_ids.clear()
                
                # ========== ERROR HANDLING: HTTP ERRORS ==========
                else: 
                    print(f"❌ [Reddit] Error {response.status_code}: {response.text}")
            
            # ========== NETWORK/PARSING ERROR HANDLING ==========
            except Exception as e:
                # Network / JSON / timeout errors
                print(f"⚠️ [Reddit] Connection Error: {e}")
            
            # Wait before next poll
            time.sleep(POLL_INTERVAL)

