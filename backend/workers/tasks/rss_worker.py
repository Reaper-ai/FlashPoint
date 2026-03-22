"""RSS Worker - Fetch RSS feeds in background

Polls RSS feeds from data_sources.json configuration.
Processes feeds in parallel and pushes to processing pipeline.
"""

import feedparser
import hashlib
import json
from datetime import datetime
from pathlib import Path
from config.celery_config import celery_app
from models.redis_client import is_duplicate, RedisPubSub
from models.database import SessionLocal, Event
from services.geo_extractor import extract_location
import sys
sys.path.append(str(Path(__file__).parent.parent))


def load_rss_config():
    """Load RSS feeds from data_sources.json"""
    config_path = Path(__file__).parent.parent.parent.parent / "data" / "data_sources.json"
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        return config.get("rss_feeds", [])
    except Exception as e:
        print(f"⚠️ Failed to load RSS config: {e}")
        return []


def compute_content_hash(text: str) -> str:
    """Generate SHA256 hash for deduplication"""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


@celery_app.task(name="tasks.rss_worker.fetch_all_rss")
def fetch_all_rss():
    """Fetch all RSS feeds from configuration"""
    feeds = load_rss_config()
    enabled_feeds = [f for f in feeds if f.get("enabled", True)]
    
    print(f"📡 Fetching {len(enabled_feeds)} RSS feeds...")
    
    for feed_config in enabled_feeds:
        try:
            fetch_single_rss.delay(feed_config)
        except Exception as e:
            print(f"⚠️ Failed to queue RSS feed {feed_config.get('name')}: {e}")
    
    return {"status": "queued", "count": len(enabled_feeds)}


@celery_app.task(name="tasks.rss_worker.fetch_single_rss")
def fetch_single_rss(feed_config: dict):
    """Fetch and process a single RSS feed"""
    name = feed_config.get("name", "Unknown")
    url = feed_config.get("url")
    bias = feed_config.get("bias", "Neutral")
    
    if not url:
        return {"status": "error", "message": "No URL provided"}
    
    try:
        # Parse RSS feed
        feed = feedparser.parse(url)
        
        if feed.bozo:  # Parse error
            print(f"⚠️ RSS parse error for {name}: {feed.bozo_exception}")
            return {"status": "error", "message": str(feed.bozo_exception)}
        
        db = SessionLocal()
        pubsub = RedisPubSub()
        new_items = 0
        
        for entry in feed.entries[:20]:  # Process last 20 items
            # Extract content
            title = entry.get("title", "")
            summary = entry.get("summary", entry.get("description", ""))
            text = f"{title}\n{summary}"
            link = entry.get("link", "")
            
            # Compute hash for deduplication
            content_hash = compute_content_hash(text)
            
            # Check if duplicate
            if is_duplicate(content_hash):
                continue
            
            # Parse timestamp
            published = entry.get("published_parsed")
            timestamp = datetime(*published[:6]) if published else datetime.utcnow()

            # Extract geo-location
            geo = extract_location(text)
            lat, lon, place = None, None, None
            if geo:
                lat = geo.get("lat")
                lon = geo.get("lon")
                place = geo.get("place")

            # Create event
            event = Event(
                source=name,
                text=text,
                url=link,
                timestamp=timestamp,
                bias=bias,
                content_hash=content_hash,
                lat=lat,
                lon=lon,
                place=place
            )

            db.add(event)
            db.flush()  # Get event ID
            new_items += 1

            # Publish to real-time stream
            pubsub.publish({
                "type": "event",
                "id": event.id,
                "source": name,
                "text": text[:200] + "..." if len(text) > 200 else text,
                "url": link,
                "timestamp": timestamp.isoformat(),
                "bias": bias,
                "lat": lat,
                "lon": lon,
                "place": place
            })
            
            # Queue for processing (embeddings, NER)
            from workers.tasks.processor import process_event
            process_event.delay(event.id)
        
        db.commit()
        db.close()
        
        print(f"✅ RSS {name}: {new_items} new items")
        return {"status": "success", "feed": name, "new_items": new_items}
        
    except Exception as e:
        print(f"❌ RSS fetch error for {name}: {e}")
        return {"status": "error", "message": str(e)}
