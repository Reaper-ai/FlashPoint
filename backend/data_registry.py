"""Data Registry: Multi-Source Intelligence Collection Pipeline

Orchestrates all data sources into unified Pathway event stream:
- News API (GNews) - news articles
- RSS Feeds - state media (Russia Today, SCMP) & western media (NYTimes, BBC)
- Reddit - public discussion forums
- Telegram - real-time messaging channels
- Simulation - test data from JSONL file

All sources normalized into unified InputSchema for downstream processing.
"""

import pathway as pw
from connectors.telegram_src import TelegramSource
from connectors.reddit_src import RedditSource
from connectors.news_src import NewsSource
from connectors.sim_src import SimulationSource
from connectors.rss_src import RssSource
import os
from dotenv import load_dotenv

# Load credentials from .env file
load_dotenv()  # This loads the variables from .env

# ========== ENVIRONMENT CREDENTIALS ==========
NEWS_API_KEY = os.getenv("GNEWS_API_KEY")
TELEGRAM_API_ID = os.getenv("TELEGRAM_API_ID")
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH")
TELEGRAM_PHONE = os.getenv("TELEGRAM_PHONE")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


# ========== UNIFIED INPUT SCHEMA ==========
# All data sources normalized to this schema for downstream processing
class InputSchema(pw.Schema):
    """Standardized event schema across all sources
    
    Attributes:
        source (str): Data origin (NewsAPI, Reddit, Telegram, RSS, Simulation)
        text (str): Main content (article, post, message)
        url (str): Source link for reference/verification
        timestamp (float): Unix timestamp of publication/ingestion
        bias (str): Source bias tag (Pro-Russia, US/Western, Independent, etc.)
    """
    source: str
    text: str
    url: str
    timestamp: float
    bias: str

def get_data_stream():
    """Build unified multi-source intelligence stream
    
    Process:
    1. Initialize individual source connectors
    2. Normalize each to InputSchema
    3. Concatenate into single Pathway table
    4. Return combined stream for RAG pipeline
    
    Sources:
    - News API: Global news (60-sec polling interval)
    - RSS Feeds: State media & Western media (300-sec polling)
    - Reddit: Public forums (60-sec polling)
    - Telegram: Real-time channels (streaming mode)
    
    Returns:
        Pathway table: Unified event stream [source, text, url, timestamp, bias]
    """
    
    # ========== SOURCE 1: NEWS API ==========
    # GNews aggregator: collects global news articles
    # Polling: 60 seconds (hourly API limits apply)
    t_news = pw.io.python.read(
        NewsSource(NEWS_API_KEY, query="world", polling_interval=60),
        schema=InputSchema, 
        name="NewsAPI Source",
        max_backlog_size=10  # Buffer max 10 items before processing
    )
   
    # ========== SOURCE 2: RSS FEEDS ==========
    # Russia Today: pro-Russia state media
    t_rss_russia = pw.io.python.read(
        RssSource("https://www.rt.com/rss/news/", source="Russia Today", bias_tag="Pro Russia"),
        schema=InputSchema, 
        name="RT RSS Feed", 
        max_backlog_size=10
    )
   
    # South China Morning Post: pro-China business/politics coverage
    t_rss_china = pw.io.python.read(
        RssSource("https://www.scmp.com/rss/318199/feed/", source="SCMP", bias_tag="Pro China"),
        schema=InputSchema, 
        name="SCMP RSS Feed", 
        max_backlog_size=10
    )

    # New York Times: Western/US-aligned coverage
    t_rss_us = pw.io.python.read(
        RssSource("https://rss.nytimes.com/services/xml/rss/nyt/World.xml", source="NYTimes", bias_tag="US/Western"),
        schema=InputSchema, 
        name="NYTimes RSS Feed",
        max_backlog_size=10
    )

    # BBC: UK/Western coverage
    t_rss_uk = pw.io.python.read(
        RssSource("https://feeds.bbci.co.uk/news/world/rss.xml", source="BBC", bias_tag="UK/Western"),
        schema=InputSchema, 
        name="BBC RSS Feed",
        max_backlog_size=10
    )
    
    # ========== SOURCE 3: TELEGRAM ==========
    # Real-time messaging from curated channels
    # Streaming mode: receives messages as they arrive (no polling)
    t_telegram = pw.io.python.read(
        TelegramSource(api_hash=TELEGRAM_API_HASH, api_id=TELEGRAM_API_ID, phone=TELEGRAM_PHONE),
        schema=InputSchema,
        mode="streaming",  # Live event subscription
        name="Telegram Source",
        max_backlog_size=10
    )
    
    # ========== SOURCE 4: REDDIT ==========
    # Public forum discussions across relevant subreddits
    # Streaming mode: monitors new posts
    t_reddit = pw.io.python.read(
        RedditSource(),
        schema=InputSchema,
        mode="streaming",
        name="Reddit Source", 
        max_backlog_size=10
    )

    # ========== MERGE RSS FEEDS ==========
    # Combine all RSS sources into single table
    t_rss_combined = t_rss_russia.concat_reindex(t_rss_china, t_rss_us, t_rss_uk)    
    
    # ========== FINAL MERGE: ALL SOURCES ==========
    # Combine News, Reddit, RSS, and Telegram into unified stream
    combined_stream = t_news.concat_reindex(t_reddit, t_rss_combined, t_telegram)
 
    return combined_stream

def get_simulation_stream():
    """Load test data stream from JSONL file for development/testing
    
    Use case:
    - Test pipeline without external API dependencies
    - Replay scenarios for debugging
    - Load-test infrastructure
    
    Returns:
        Pathway table: Simulation events in InputSchema format
    """
    sim_path = "data/dummy.jsonl"
    
    # Initialize simulation source with 10-second inter-event delay
    t_sim = pw.io.python.read(
        SimulationSource(file_path=sim_path, interval=10),
        schema=InputSchema,
        autocommit_duration_ms=1000,  # Process batches every 1 second
        name="Simulation Source",
        max_backlog_size=10
    )

    pw.io.csv
    return t_sim

