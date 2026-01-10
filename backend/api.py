from fastapi import FastAPI
import uvicorn
from typing import Dict, Any
from collections import deque
import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

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
    """Simple keyword matching to find lat/lon."""
    if not text: return None
    for place, coords in GEO_LOCATIONS.items():
        if place in text or place.lower() in text.lower():
            return coords
    return None


# --- 1. SETUP GEMINI (For Reports) ---

genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel('gemini-flash-latest')

app = FastAPI()

# 1. In-Memory Buffer to store recent items (Push-based)
# Stores the last 20 items received from Pathway
latest_news = deque(maxlen=100)

@app.get("/")
def read_root():
    return {"status": "Flashpoint Receiver Online"}

# 2. THE FIX: Accept JSON Body
@app.post("/v1/stream")
async def receive_stream(data: Dict[str, Any]):
    
    coords = extract_location(data['text'])
    if coords:
        data["lat"] = coords["lat"]
        data["lon"] = coords["lon"]
            
    latest_news.append(data)
       
    return {"status": "received", "count": len(data)}

# 3. New Endpoint for Frontend to POLL
@app.get("/v1/frontend/feed")
def get_feed():
    """
    The Streamlit frontend calls THIS to get the data.
    """
    return list(latest_news)
# ... (Previous imports) ...

# --- 1. REPORT GENERATION ---
@app.get("/v1/generate_report")
def generate_report():
    """Generates a formal intelligence briefing on a topic."""

    # 2. Prompt for Report Format

    context_text = "\n".join([f"- {d['text']}" for d in latest_news])
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
    
    # 3. Generate
    response = gemini_model.generate_content(prompt)
    #4. Return Text
    return {"report": response.text}



if __name__ == "__main__":
    # Ensure port matches what you put in Pathway (8000)
    uvicorn.run(app, host="0.0.0.0", port=8000)