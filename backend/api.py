from fastapi import FastAPI, Request
import uvicorn
from typing import List, Dict, Any
from collections import deque
import requests
import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

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
    prompt = f"""ROLE : "You are a senior intelligence analyst. Write a formal SITREP (Situation Report).
        TOPIC: give summary of major key happenings around the world
        
        INTELLIGENCE DATA:
        {context_text}
        
        OUTPUT FORMAT:
        1. EXECUTIVE SUMMARY
        2. KEY EVENTS
        4. FORECAST
        """
    
    # 3. Generate
    response = gemini_model.generate_content(prompt)
    #4. Return Text
    return {"report": response}



if __name__ == "__main__":
    # Ensure port matches what you put in Pathway (8000)
    uvicorn.run(app, host="0.0.0.0", port=8000)