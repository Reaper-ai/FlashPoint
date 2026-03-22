"""Event Processor - Generate embeddings and store in Qdrant

Processes events through:
1. Text cleaning
2. Embedding generation (sentence-transformers)
3. Vector storage (Qdrant)
"""

from config.celery_config import celery_app
from models.database import SessionLocal, Event
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import hashlib
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize embedding model (lazy load)
_embedding_model = None
_qdrant_client = None

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
COLLECTION_NAME = "flashpoint_events"


def get_embedding_model():
    """Lazy load embedding model"""
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL)
    return _embedding_model


def get_qdrant_client():
    """Lazy load Qdrant client"""
    global _qdrant_client
    if _qdrant_client is None:
        _qdrant_client = QdrantClient(url=QDRANT_URL)
        
        # Create collection if not exists
        try:
            _qdrant_client.get_collection(COLLECTION_NAME)
        except:
            _qdrant_client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE)
            )
            print(f"✅ Created Qdrant collection: {COLLECTION_NAME}")
    
    return _qdrant_client


@celery_app.task(name="tasks.processor.process_event")
def process_event(event_id: int):
    """Process event: generate embeddings and extract entities"""
    try:
        db = SessionLocal()
        event = db.query(Event).filter(Event.id == event_id).first()
        
        if not event:
            print(f"⚠️ Event {event_id} not found")
            return {"status": "error", "message": "Event not found"}
        
        # Skip if already processed
        if event.embedding_id:
            return {"status": "skipped", "message": "Already processed"}
        
        # Generate embedding
        model = get_embedding_model()
        embedding = model.encode(event.text).tolist()
        
        # Store in Qdrant
        qdrant = get_qdrant_client()
        point_id = hashlib.md5(f"{event.id}:{event.timestamp}".encode()).hexdigest()
        
        qdrant.upsert(
            collection_name=COLLECTION_NAME,
            points=[
                PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        "event_id": event.id,
                        "source": event.source,
                        "text": event.text[:500],  # Store truncated for search
                        "url": event.url,
                        "timestamp": event.timestamp.isoformat(),
                        "bias": event.bias
                    }
                )
            ]
        )
        
        # Update event with embedding ID
        event.embedding_id = point_id

        db.commit()
        db.close()

        print(f"✅ Processed event {event_id}")
        return {"status": "success", "event_id": event_id, "embedding_id": point_id}
        
    except Exception as e:
        print(f"❌ Processing error for event {event_id}: {e}")
        return {"status": "error", "message": str(e)}


@celery_app.task(name="tasks.processor.batch_process_events")
def batch_process_events(event_ids: list):
    """Process multiple events in batch"""
    results = []
    for event_id in event_ids:
        result = process_event(event_id)
        results.append(result)
    return results
