#!/usr/bin/env python3
"""Initialize FlashPoint Infrastructure

Sets up database tables, Qdrant collections, and performs health checks.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from models.database import init_db, init_timescaledb, engine
from models.redis_client import redis_health_check
from workers.tasks.processor import get_qdrant_client
import asyncio
from sqlalchemy import text

def check_postgresql():
    """Check PostgreSQL connection"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print(f"✅ PostgreSQL: {version[:50]}...")
            return True
    except Exception as e:
        print(f"❌ PostgreSQL: {e}")
        return False


def check_redis():
    """Check Redis connection"""
    if redis_health_check():
        print("✅ Redis: Connected")
        return True
    else:
        print("❌ Redis: Connection failed")
        return False


def check_qdrant():
    """Check Qdrant connection"""
    try:
        client = get_qdrant_client()
        collections = client.get_collections()
        print(f"✅ Qdrant: Connected ({len(collections.collections)} collections)")
        return True
    except Exception as e:
        print(f"❌ Qdrant: {e}")
        return False


def main():
    """Run all initialization checks"""
    print("=" * 60)
    print("FlashPoint Infrastructure Initialization")
    print("=" * 60)
    
    print("\n[1/4] Checking PostgreSQL...")
    pg_ok = check_postgresql()
    
    print("\n[2/4] Checking Redis...")
    redis_ok = check_redis()
    
    print("\n[3/4] Checking Qdrant...")
    qdrant_ok = check_qdrant()
    
    print("\n[4/4] Initializing Database Tables...")
    if pg_ok:
        try:
            init_db()
            print("✅ Database tables created")
            
            print("\nSetting up TimescaleDB...")
            init_timescaledb()
            
        except Exception as e:
            print(f"❌ Database initialization failed: {e}")
    
    print("\n" + "=" * 60)
    print("Summary:")
    print(f"  PostgreSQL: {'✅' if pg_ok else '❌'}")
    print(f"  Redis:      {'✅' if redis_ok else '❌'}")
    print(f"  Qdrant:     {'✅' if qdrant_ok else '❌'}")
    print("=" * 60)
    
    if not all([pg_ok, redis_ok, qdrant_ok]):
        print("\n⚠️  Some services are not available.")
        print("   Run: docker-compose up -d")
        sys.exit(1)
    else:
        print("\n✅ All systems ready!")
        print("\nNext steps:")
        print("  1. Start Celery worker: celery -A celery_config worker -l info")
        print("  2. Start Celery beat: celery -A celery_config beat -l info")
        print("  3. Start FastAPI: python main.py")
        sys.exit(0)


if __name__ == "__main__":
    main()
