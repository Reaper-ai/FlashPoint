<<<<<<< HEAD
"""FastAPI Backend Service for FlashPoint Intelligence Engine

Responsibilities:
- Receives real-time event stream from Pathway (news, Reddit, Telegram, RSS)
- Serves events to frontend dashboard via polling
- Generates intelligence reports using Google Gemini API
- Extracts geolocation data from events for mapping visualization
"""

from fastapi import FastAPI, Request
=======
from fastapi import FastAPI
>>>>>>> a984c70811017dafea27637922b08cfdb71f385b
import uvicorn
from typing import Dict, Any
from collections import deque
import google.generativeai as genai
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ========== GEOLOCATION REFERENCE DATA ==========
# Mapping of place names to geographic coordinates
# Used to extract lat/lon from event text for map visualization
GEO_LOCATIONS = {
    "Kyiv": {"lat": 50.4501, "lon": 30.5234},
    "Ukraine": {"lat": 48.3794, "lon": 31.1656},
    "Moscow": {"lat": 55.7558, "lon": 37.6173},
    "Russia": {"lat": 61.5240, "lon": 105.3188},
    "Washington": {"lat": 38.9072, "lon": -77.0369},
    "USA": {"lat": 37.0902, "lon": -95.7129},
    "Beijing": {"lat": 39.9042, "lon": 116.4074},
    "China": {"lat": 35.8617, "lon": 104.1954},
    "Gaza": {"lat": 31.5, "lon": 34.466},
    "Israel": {"lat": 31.0461, "lon": 34.8516},
    "Taiwan": {"lat": 23.6978, "lon": 120.9605},
    "London": {"lat": 51.5074, "lon": -0.1278},
    "Tehran": {"lat": 35.6892, "lon": 51.3890},
    "Iran": {"lat": 32.4279, "lon": 53.6880},
    "Delhi": {"lat": 28.6139, "lon": 77.2090},
    "India": {"lat": 20.5937, "lon": 78.9629},
}



def extract_location(text):
    """Extract geolocation coordinates from event text via keyword matching
    
    Strategy: Simple string matching against known place names
    - Case-insensitive matching
    - Returns first match found
    - Suitable for rapid preprocessing in high-throughput scenarios
    
    Args:
        text (str): Event text (title + description)
    
    Returns:
        dict or None: {"lat": float, "lon": float} if location found, else None
    """
    if not text:
        return None
    
    # Perform keyword matching against geolocation reference data
    for place, coords in GEO_LOCATIONS.items():
        if place in text or place.lower() in text.lower():
            return coords
    return None


# ========== GEMINI AI SETUP ==========
# Configure Google Generative AI for intelligence report generation
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel('gemini-flash-latest')

# ========== FASTAPI APPLICATION SETUP ==========
app = FastAPI()

# ========== IN-MEMORY EVENT BUFFER ==========
# Stores recent events from Pathway (FIFO, max 100 items)
# Enables frontend polling to retrieve latest updates
latest_news = deque(maxlen=100)

@app.get("/")
def read_root():
    """Health check endpoint - confirms API is running"""
    return {"status": "Flashpoint Receiver Online"}

# ========== EVENT INGESTION ENDPOINT ==========
@app.post("/v1/stream")
async def receive_stream(data: Dict[str, Any]):
    """Receive structured events from Pathway data pipeline
    
    Flow:
    1. Extract geolocation from event text if present
    2. Augment event with lat/lon coordinates
    3. Store in memory buffer for frontend polling
    
    Args:
        data: Event dict with keys [source, text, url, timestamp, bias]
    
    Returns:
        dict: Acknowledgment with event count in buffer
    """
    # Attempt geolocation extraction for map visualization
    coords = extract_location(data['text'])
    if coords:
        # Augment event with geographic coordinates
        data["lat"] = coords["lat"]
        data["lon"] = coords["lon"]
            
    # Append to circular buffer (auto-evicts oldest if full)
    latest_news.append(data)
       
    return {"status": "received", "count": len(data)}

# ========== EVENT POLLING ENDPOINT ==========
@app.get("/v1/frontend/feed")
def get_feed():
    """Provide event stream to frontend dashboard via polling
    
    Frontend periodically calls this to fetch new events
    Returns entire buffer contents (frontend handles display logic)
    
    Returns:
        list: Array of event dicts sorted by ingestion order (oldest first)
    """
    return list(latest_news)

# ========== INTELLIGENCE REPORT GENERATION ==========
@app.get("/v1/generate_report")
def generate_report():
<<<<<<< HEAD
    """Generate formal intelligence briefing from event stream
=======
    """Generates a formal intelligence briefing on a topic."""

    # 2. Prompt for Report Format

    context_text = "\n".join([f"- {d['text']}-{d['source']}-{d['bias']}" for d in latest_news])
    prompt = f""" TASK: Synthesize the provided 'Raw Intel' into a professional News Briefing. 
        CONSTRAINTS:
        1. Use ONLY the provided text below. Do NOT fill in missing data like names, dates, or events not present.
        2. Tone: Objective, Journalistic, Concise.
        3. Cite the source name in brackets [Source] for every claim.
        4. Reply in plain text, do not give response in markdown
    
        RAW INTEL:
        {context_text}
    
        REQUIRED OUTPUT FORMAT:
        ##  Global Situation Summary
        [Write a 2-3 sentence executive summary of the provided text]

        ## Key Developments
        - **[Category/Region]**: [Detail] [Source]
        - **[Category/Region]**: [Detail] [Source]
    
        ## Outlook
        [Short forecast based *only* on the provided trends]
    """
>>>>>>> a984c70811017dafea27637922b08cfdb71f385b
    
    Process:
    1. Extract textual content from all buffered events
    2. Construct system prompt for SITREP generation
    3. Query Gemini with context and structured output request
    4. Return formatted briefing (Executive Summary, Key Events, Forecast)
    
    Returns:
        dict: {"report": str} - Formatted SITREP from LLM
    """
    # Combine all event texts into context block for LLM
    context_text = "\n".join([f"- {d['text']}" for d in latest_news])
    
    # Construct prompt with role, context, and output format specification
    prompt = f"""ROLE: "You are a senior intelligence analyst. Write a formal SITREP (Situation Report).
TOPIC: Give summary of major key happenings around the world

INTELLIGENCE DATA:
{context_text}

OUTPUT FORMAT:
1. EXECUTIVE SUMMARY
2. KEY EVENTS
3. FORECAST
"""
    
    # Query Gemini to generate structured report
    response = gemini_model.generate_content(prompt)
    
    # Return formatted response
    return {"report": response.text}



if __name__ == "__main__":
    """Entry point: Start FastAPI server
    
    Configuration:
    - Host: 0.0.0.0 (listen on all interfaces)
    - Port: 8000 (Pathway writes to /v1/stream, frontend polls /v1/frontend/feed)
    """
    uvicorn.run(app, host="0.0.0.0", port=8000)