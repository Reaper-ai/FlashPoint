"""Telegram Worker - Real-time message streaming

Streams Telegram messages in real-time using Telethon.
Runs as a long-lived Celery task.
"""

from config.celery_config import celery_app
from models.database import SessionLocal, Event
from models.redis_client import is_duplicate, RedisPubSub
from services.geo_extractor import extract_location
import hashlib
from datetime import datetime
import os
from dotenv import load_dotenv
import asyncio

load_dotenv()

TELEGRAM_API_ID = os.getenv("TELEGRAM_API_ID")
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH")
TELEGRAM_PHONE = os.getenv("TELEGRAM_PHONE")


@celery_app.task(name="tasks.telegram_worker.start_telegram_stream", bind=True)
def start_telegram_stream(self):
    """Start Telegram real-time streaming (long-lived task)"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(telegram_stream_async())
    finally:
        loop.close()


async def telegram_stream_async():
    """Async Telegram streaming"""
    try:
        from telethon import TelegramClient, events
        import json
        from pathlib import Path
        
        # Load channel configuration
        config_path = Path(__file__).parent.parent.parent.parent / "data" / "data_sources.json"
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        tg_config = config.get("telegram_sources", [])
        if not tg_config or not tg_config[0].get("enabled"):
            print("⚠️ Telegram source disabled")
            return {"status": "disabled"}
        
        channels = [ch["handle"] for ch in tg_config[0].get("channels", [])]
        bias_tags = {ch["handle"]: ch.get("bias", "Independent") 
                    for ch in tg_config[0].get("channels", [])}
        
        # Create Telegram client
        client = TelegramClient('session_flashpoint', 
                               TELEGRAM_API_ID, 
                               TELEGRAM_API_HASH)
        
        @client.on(events.NewMessage(chats=channels))
        async def handler(event):
            """Handle new Telegram messages"""
            try:
                text = str(event.text)
                if not text:
                    return
                
                # Compute hash
                content_hash = hashlib.sha256(text.encode()).hexdigest()
                
                # Check duplicate
                if is_duplicate(content_hash):
                    return
                
                # Get sender info
                sender = await event.get_sender()
                username = sender.username if sender else "Unknown"

                # Extract geo-location
                geo = extract_location(text)
                lat, lon, place = None, None, None
                if geo:
                    lat = geo.get("lat")
                    lon = geo.get("lon")
                    place = geo.get("place")

                # Create event
                db = SessionLocal()
                event_obj = Event(
                    source="Telegram",
                    text=text,
                    url=f"https://t.me/{username}/{event.id}",
                    timestamp=datetime.fromtimestamp(event.date.timestamp()),
                    bias=bias_tags.get(username, "Independent"),
                    content_hash=content_hash,
                    lat=lat,
                    lon=lon,
                    place=place
                )

                db.add(event_obj)
                db.flush()  # Get event ID
                event_id = event_obj.id
                db.commit()
                db.close()

                # Publish to stream
                pubsub = RedisPubSub()
                pubsub.publish({
                    "type": "event",
                    "id": event_id,
                    "source": f"Telegram/{username}",
                    "text": text[:200] + "..." if len(text) > 200 else text,
                    "url": event_obj.url,
                    "timestamp": event_obj.timestamp.isoformat(),
                    "bias": event_obj.bias,
                    "lat": lat,
                    "lon": lon,
                    "place": place
                })
                
                # Queue for processing
                from workers.tasks.processor import process_event
                process_event.delay(event_id)
                
                print(f"⚡ Telegram [{username}]: New message")
                
            except Exception as e:
                print(f"❌ Telegram handler error: {e}")
        
        # Connect and run
        await client.start(phone=TELEGRAM_PHONE)
        print(f"✅ Telegram: Connected, monitoring {len(channels)} channels")
        await client.run_until_disconnected()
        
    except Exception as e:
        print(f"❌ Telegram stream error: {e}")
        return {"status": "error", "message": str(e)}
