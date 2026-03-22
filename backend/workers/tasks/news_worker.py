"""News API Worker - Fetch articles from GNews

Uses GNews API to fetch world news articles.
"""

import requests
import hashlib
from datetime import datetime
from pathlib import Path
import json
import os
from dotenv import load_dotenv
from config.celery_config import celery_app
from models.redis_client import is_duplicate, RedisPubSub
from models.database import SessionLocal, Event
from services.geo_extractor import extract_location

load_dotenv()

NEWS_API_KEY = os.getenv("GNEWS_API_KEY")


def load_news_config():
    """Load News API config"""
    config_path = Path(__file__).parent.parent.parent.parent / "data" / "data_sources.json"
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        news_sources = config.get("news_sources", [])
        if news_sources:
            return news_sources[0]
        return {}
    except Exception as e:
        print(f"⚠️ Failed to load News config: {e}")
        return {}


@celery_app.task(name="tasks.news_worker.fetch_news")
def fetch_news():
    """Fetch news articles from GNews API"""
    config = load_news_config()
    
    if not config.get("enabled", True):
        return {"status": "disabled"}
    
    if not NEWS_API_KEY:
        print("⚠️ GNews API key not configured")
        return {"status": "error", "message": "No API key"}
    
    query = config.get("query", "world conflict war geopolitics")
    url = f"https://gnews.io/api/v4/search"
    
    params = {
        "q": query,
        "token": NEWS_API_KEY,
        "lang": "en",
        "max": 20
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code != 200:
            return {"status": "error", "code": response.status_code}
        
        data = response.json()
        articles = data.get("articles", [])
        
        db = SessionLocal()
        pubsub = RedisPubSub()
        new_articles = 0
        
        for article in articles:
            title = article.get("title", "")
            description = article.get("description", "")
            content = article.get("content", "")
            
            full_text = f"{title}\n{description}\n{content}"
            
            # Compute hash
            content_hash = hashlib.sha256(full_text.encode()).hexdigest()
            
            # Check duplicate
            if is_duplicate(content_hash):
                continue
            
            # Parse timestamp
            published = article.get("publishedAt")
            timestamp = datetime.fromisoformat(published.replace("Z", "+00:00")) if published else datetime.utcnow()

            # Extract geo-location
            geo = extract_location(full_text)
            lat, lon, place = None, None, None
            if geo:
                lat = geo.get("lat")
                lon = geo.get("lon")
                place = geo.get("place")

            # Create event
            event = Event(
                source="NewsAPI",
                text=full_text,
                url=article.get("url", ""),
                timestamp=timestamp,
                bias="Varied",
                content_hash=content_hash,
                lat=lat,
                lon=lon,
                place=place
            )

            db.add(event)
            db.flush()  # Get event ID
            new_articles += 1

            # Publish to stream
            pubsub.publish({
                "type": "event",
                "id": event.id,
                "source": "NewsAPI",
                "text": full_text[:200] + "..." if len(full_text) > 200 else full_text,
                "url": event.url,
                "timestamp": timestamp.isoformat(),
                "bias": "Varied",
                "lat": lat,
                "lon": lon,
                "place": place
            })
            
            # Queue for processing
            from workers.tasks.processor import process_event
            process_event.delay(event.id)
        
        db.commit()
        db.close()
        
        print(f"✅ NewsAPI: {new_articles} new articles")
        return {"status": "success", "new_articles": new_articles}
        
    except Exception as e:
        print(f"❌ NewsAPI fetch error: {e}")
        return {"status": "error", "message": str(e)}
