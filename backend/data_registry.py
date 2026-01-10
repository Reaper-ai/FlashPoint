import pathway as pw
from connectors.telegram_src import TelegramSource
from connectors.reddit_src import RedditSource
from connectors.news_src import NewsSource
from connectors.sim_src import SimulationSource
from connectors.rss_src import RssSource
import os
import json
from dotenv import load_dotenv

load_dotenv()  # This loads the variables from .env

NEWS_API_KEY = os.getenv("GNEWS_API_KEY")
TELEGRAM_API_ID = os.getenv("TELEGRAM_API_ID")
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH")
TELEGRAM_PHONE = os.getenv("TELEGRAM_PHONE")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


class InputSchema(pw.Schema):
        source: str
        text: str
        url: str
        timestamp: float
        bias: str

def get_data_stream():
   # 1. News API Source (12 hour delay)
    t_news = pw.io.python.read(
        NewsSource(NEWS_API_KEY, query="world", polling_interval=60),
        schema=InputSchema, name="NewsAPI Source" , max_backlog_size=10
    )
   
    # 2. RSS Feeds from State Media + Western Media
    t_rss_russia = pw.io.python.read(
        RssSource("https://www.rt.com/rss/news/", source="Russia Today", bias_tag="Pro Russia"),
        schema=InputSchema, name="RT RSS Feed", max_backlog_size=10
    )
   
    t_rss_china = pw.io.python.read(
        RssSource("https://www.scmp.com/rss/318199/feed/", source="SCMP", bias_tag="Pro China"),
        schema=InputSchema, name="SCMP RSS Feed", max_backlog_size=10
    )

    t_rss_us = pw.io.python.read(
        RssSource("https://rss.nytimes.com/services/xml/rss/nyt/World.xml", source="NYTimes", bias_tag="US/Western"),
        schema=InputSchema, name="NYTimes RSS Feed" , max_backlog_size=10
    )

    t_rss_uk = pw.io.python.read(
        RssSource("https://feeds.bbci.co.uk/news/world/rss.xml", source="BBC", bias_tag="UK/Western"),
        schema=InputSchema, name="BBC RSS Feed" , max_backlog_size=10
    )
    
    # 3. Telegram Source
    t_telegram = pw.io.python.read(
        TelegramSource(api_hash=TELEGRAM_API_HASH, api_id=TELEGRAM_API_ID, phone=TELEGRAM_PHONE),
        schema=InputSchema,
        mode="streaming", name="Telegram Source" , max_backlog_size=10
    )
    
    # 3. Reddit Source
    t_reddit = pw.io.python.read(
        RedditSource(),
        schema=InputSchema,
        mode="streaming", name="Reddit Source", max_backlog_size=10
    )

    t_rss_combined = t_rss_russia.concat_reindex(t_rss_china, t_rss_us, t_rss_uk)    
    combined_stream = t_news.concat_reindex(t_reddit, t_rss_combined, t_telegram)
 
    return combined_stream

def get_simulation_stream():
    sim_path = "data/dummy.jsonl"
    t_sim = pw.io.python.read(
        SimulationSource(file_path=sim_path, interval=10),
        schema=InputSchema,
        autocommit_duration_ms=1000, name="Simulation Source" , max_backlog_size=10
    )

    pw.io.csv
    return t_sim

