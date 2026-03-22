from __future__ import annotations

import asyncio
import json
import logging
from collections import deque
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from models.database import SessionLocal, Event
from models.redis_client import redis_binary
from services.geo_extractor import extract_location
from services.report_service import generate_pdf_bytes, generate_sitrep
from services.commodity_service import get_commodity_service
from services.conflict_service import get_conflict_service
from services.rag_service import get_rag_service
from services.tracking_service import fetch_flights, get_ships, get_flights, stream_ships

logger = logging.getLogger(__name__)

_FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend" / "web"
_ASSETS_DIR   = Path(__file__).resolve().parent.parent / "frontend" / "assets"

latest_news: deque[Dict[str, Any]] = deque(maxlen=100)

@asynccontextmanager
async def lifespan(app):
    # Start AIS ship stream in background
    asyncio.create_task(stream_ships())
    yield

app = FastAPI(title="FlashPoint Intel API", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Health ────────────────────────────────────────────────────────────

@app.get("/health", tags=["meta"])
def health():
    return {"status": "online", "buffer_size": len(latest_news)}


# ── Events API ────────────────────────────────────────────────────────

@app.get("/api/events/recent", tags=["frontend"])
def get_recent_events(limit: int = 50):
    try:
        db = SessionLocal()
        events = db.query(Event).order_by(Event.timestamp.desc()).limit(limit).all()
        db.close()
        result = [
            {
                "id": e.id,
                "source": e.source,
                "text": e.text,
                "url": e.url,
                "bias": e.bias,
                "lat": e.lat,
                "lon": e.lon,
                "place": e.place,
                "timestamp": e.timestamp.isoformat(),
            }
            for e in events
        ]
        return {"success": True, "events": result, "count": len(result)}
    except Exception as exc:
        logger.exception("Failed to fetch recent events")
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/events/stream", tags=["frontend"])
async def events_sse_stream(request: Request):
    async def stream():
        pubsub = redis_binary.pubsub()
        pubsub.subscribe("flashpoint:events")
        try:
            while True:
                if await request.is_disconnected():
                    break
                msg = pubsub.get_message(timeout=1.0)
                if msg and msg["type"] == "message":
                    yield f"data: {msg['data'].decode()}\n\n"
                else:
                    yield ": keep-alive\n\n"
                await asyncio.sleep(0.5)
        finally:
            pubsub.unsubscribe("flashpoint:events")

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ── Commodities ───────────────────────────────────────────────────────

@app.get("/api/commodities/latest", tags=["commodities"])
async def get_commodity_prices(symbols: str = None):
    try:
        service = get_commodity_service()
        symbol_list = symbols.split(",") if symbols else None
        data = await service.fetch_prices(symbol_list)
        return Response(
            content=json.dumps(data),
            media_type="application/json",
            headers={"Cache-Control": "public, max-age=300"},
        )
    except Exception as e:
        logger.exception("Commodity API error")
        raise HTTPException(status_code=500, detail=str(e))


# ── Conflicts ─────────────────────────────────────────────────────────

@app.get("/api/conflicts/all", tags=["conflicts"])
async def get_all_conflicts(refresh: bool = False):
    try:
        service = get_conflict_service()
        data = await service.get_conflicts(force_refresh=refresh)
        return Response(
            content=json.dumps(data),
            media_type="application/json",
            headers={"Cache-Control": "public, max-age=300"},
        )
    except Exception as e:
        logger.exception("Conflicts API error")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/conflicts/{conflict_id}", tags=["conflicts"])
async def get_conflict_details(conflict_id: int):
    try:
        service = get_conflict_service()
        conflict = service.get_conflict_by_id(conflict_id)
        if not conflict:
            raise HTTPException(status_code=404, detail="Conflict not found")
        return {"success": True, "conflict": conflict}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Conflict details error")
        raise HTTPException(status_code=500, detail=str(e))


# ── Reports ───────────────────────────────────────────────────────────

@app.get("/v1/generate_report", tags=["intel"])
async def generate_report():
    if not latest_news:
        raise HTTPException(status_code=400, detail="No intelligence data in buffer yet.")
    try:
        items = list(latest_news)
        loop = asyncio.get_event_loop()
        report = await loop.run_in_executor(None, generate_sitrep, items)
    except Exception as exc:
        logger.exception("Report generation failed")
        raise HTTPException(status_code=503, detail=f"Report generation failed: {exc}")
    return {"report": report}


@app.get("/v1/generate_report/pdf", tags=["intel"])
async def generate_report_pdf():
    if not latest_news:
        raise HTTPException(status_code=400, detail="No intelligence data in buffer yet.")
    try:
        items = list(latest_news)
        loop = asyncio.get_event_loop()
        pdf_bytes = await loop.run_in_executor(None, generate_pdf_bytes, items)
    except Exception as exc:
        logger.exception("PDF generation failed")
        raise HTTPException(status_code=503, detail=f"PDF generation failed: {exc}")

    from datetime import datetime, timezone
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="SITREP_{ts}.pdf"'},
    )


# ── Chat ──────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    history: List[Dict[str, str]] = []


@app.post("/v1/chat", tags=["intel"])
async def chat(req: ChatRequest):
    async def token_stream():
        try:
            rag = get_rag_service()
            async for token in rag.query_streaming(req.message):
                yield f"data: {json.dumps({'token': token})}\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"
        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        token_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ── Legacy Pathway ingestion endpoint (kept for compatibility) ────────

@app.post("/v1/stream", tags=["pipeline"])
async def receive_stream(data: Dict[str, Any]):
    text = data.get("text", "")
    geo = extract_location(text)
    if geo:
        data.setdefault("lat", geo["lat"])
        data.setdefault("lon", geo["lon"])
        data.setdefault("place", geo["place"])
    latest_news.append(data)
    return {"status": "received"}


@app.get("/api/tracking/flights", tags=["tracking"])
async def get_flight_data(military_only: bool = False, limit: int = 50):
    """Get flight tracking data (limited and cached)"""
    flights = await fetch_flights()
    if military_only:
        flights = [f for f in flights if f.get("military")]

    # Limit results to prevent frontend lag
    flights = flights[:limit]

    return {"success": True, "count": len(flights), "flights": flights}

@app.get("/api/tracking/ships", tags=["tracking"])
async def get_ship_data(tankers_only: bool = False, limit: int = 100):
    """Get ship tracking data (limited and cached)"""
    ships = get_ships(tankers_only)

    # Limit results to prevent frontend lag
    ships = ships[:limit]

    return {"success": True, "count": len(ships), "ships": ships}

# ── Static mount — MUST BE LAST ───────────────────────────────────────
if _ASSETS_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=str(_ASSETS_DIR)), name="assets")
if _FRONTEND_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(_FRONTEND_DIR), html=True), name="frontend")
else:
    logger.warning("Frontend dir not found at %s — static serving disabled.", _FRONTEND_DIR)