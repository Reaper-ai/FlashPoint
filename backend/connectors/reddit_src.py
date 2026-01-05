import time
import requests
import pathway as pw 
from datetime import datetime

SUBREDDITS = "worldnews+geopolitics+technology+artificialintelligence"
POST_LIMIT = 50
POLL_INTERVAL = 60 # Seconds (Safe rate limit)

class RedditSource(pw.io.python.ConnectorSubject):
    def run(self):
        """
        Polls Reddit JSON API and pushes data to Pathway.
        """
        seen_ids=set()

        url = f"https://www.reddit.com/r/{SUBREDDITS}/new.json?limit={POST_LIMIT}"

        headers={
            'User-Agent': 'FlashPointEngine/1.0 (Macintosh; Intel Mac OS X 10_15_7)'
        }
        print(f"📡 [Reddit] Engine started. Monitoring: r/{SUBREDDITS}")
        while True:
            try:
                response=requests.get(url,headers=headers,timeout=10)
                #handleing rate limits
                if response.status_code==429:
                    print("⚠️ [Reddit] Rate Limited! Cooling down for 2 minutes...")
                    time.sleep(120)
                    continue
                
                # handle success
                if response.status_code==200:
                    data=response.json()
                    posts=data.get('data',{}).get('children',[])
                    new_count=0

                    #3 procces posts (newest first )
                    for item in posts:
                        post=item.get('data',{})
                        post_id=post.get('id')

                        #deduplication : only  proceess if we havent see this id 
                        if post_id not in seen_ids:
                            seen_ids.add(post_id)
                            new_count+=1

                            # Extracting text(body + link)
                            title=post.get('title','').strip()
                            is_text_post=post.get('is_self',False)
                            body=post.get('selftext','').strip() if is_text_post else ""

                            # combination for ai content
                            full_text=f"{title}\n{body}"


                            # pathway easiness
                            row={"source":"reddit",
                                 "author": str(post.get('author')),
                                 "text": full_text,
                                 "url": f"https://reddit.com{post.get('permalink')}",
                                 "raw_timestamp": float(post.get('created_utc',0)),
                                 "ingested_at":datetime.now().isoformat()
                                 }
                            # sending to engine 
                            self.next(**row)
                            print(f"👾 [Reddit] {title[:40]}...", flush=True)
                        if len(seen_ids)>5000:
                            seen_ids.clear()
                else: 
                    print(f"❌ [Reddit] Error {response.status_code}: {response.text}")
            
            except Exception as e:
                print(f"⚠️ [Reddit] Connection Error: {e}")
            time.sleep(POLL_INTERVAL)

