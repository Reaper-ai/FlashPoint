import pathway as pw
from connectors.telegram_src import TelegramSource
from connectors.reddit_src import RedditSource
from connectors.news_src import NewsSource
from connectors.sim_src import SimulationSource
from connectors.rss_src import RssSource


import os
from dotenv import load_dotenv

load_dotenv()  # This loads the variables from .env

NEWS_API_KEY = os.getenv("GNEWS_API_KEY")
TELEGRAM_API_ID = os.getenv("TELEGRAM_API_ID")
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH")
TELEGRAM_PHONE = os.getenv("TELEGRAM_PHONE")


God_Mode =  True # Set to True to enable simulation mode

def run():
    print(" Flashpoint Engine Starting (Multi-Source Mode)...")

    # Unified Schema
    class InputSchema(pw.Schema):
        source: str
        text: str
        url: str
        timestamp: float
        bias: str

    # 1. News API Source (12 hour delay)
    t_news = pw.io.python.read(
        NewsSource(NEWS_API_KEY, query="world", polling_interval=60),
        schema=InputSchema
    )
   
    # 2. RSS Feeds from State Media + Western Media
    t_rss_russia = pw.io.python.read(
        RssSource("https://www.rt.com/rss/news/", source="Russia Today", bias_tag="Russia/Eastern"),
        schema=InputSchema
    )
   
    t_rss_china = pw.io.python.read(
        RssSource("https://www.cgtn.com/subscribe/rss/section/world.xml", source="CGTN", bias_tag="China/Eastern"),
        schema=InputSchema
    )

    t_rss_us = pw.io.python.read(
        RssSource("https://rss.nytimes.com/services/xml/rss/nyt/World.xml", source="NYTimes", bias_tag="US/Western"),
        schema=InputSchema
    )

    t_rss_uk = pw.io.python.read(
        RssSource("https://feeds.bbci.co.uk/news/world/rss.xml", source="BBC", bias_tag="UK/Western"),
        schema=InputSchema
    )

    t_rss_combined = t_rss_russia.concat_reindex(t_rss_china, t_rss_us, t_rss_uk)    
    
    # 3. Telegram Source
    t_telegram = pw.io.python.read(
        TelegramSource(api_hash=TELEGRAM_API_HASH, api_id=TELEGRAM_API_ID, phone=TELEGRAM_PHONE),
        schema=InputSchema,
        mode="streaming"
    )

    # 3. Reddit Source
    t_reddit = pw.io.python.read(
        RedditSource(),
        schema=InputSchema,
        mode="streaming"
    )


    # --- THE FIX ---
    # We explicitly promise Pathway that Reddit and Telegram are separate streams.
    # This satisfies the "disjoint" requirement.
    
    t_reddit = t_reddit.promise_universes_are_disjoint(t_telegram)
    #combined_stream = t_news.concat_reindex(t_reddit, t_rss_combined, t_telegram)
    combined_stream = t_news.concat_reindex(t_reddit, t_rss_combined)   
    
        
    if God_Mode:
        # Simulation Source (The "God Mode" Stream)
        # Pointing to the file you created in Step 1
        sim_path = "data/dummy.jsonl"
        t_sim = pw.io.python.read(
        SimulationSource(file_path=sim_path, interval=10),
        schema=InputSchema,
        autocommit_duration_ms=1000
        )

        combined_stream = combined_stream.concat_reindex(t_sim)

    pw.io.csv.write(combined_stream, "output_unified.csv")

    print("✅ Pipeline configured. Listening to World News & Telegram Channels...")
    pw.run()



if __name__ == "__main__":
    run()

    # # 1. Real Sources (Comment out if testing offline)
    # # t_news = ...
    
    # # 2. Simulation Source (The "God Mode" Stream)
    # # Pointing to the file you created in Step 1
    # t_sim = pw.io.python.read(
    #     SimulationSource("data/crisis_scenario.jsonl", interval=5),
    #     schema=schema
    # )

    # # 3. Combine (or just use t_sim for testing)
    # # combined_stream = t_news + t_sim
    # # For now, let's just run the simulation to test:
    # combined_stream = t_sim
    
    # # ... (Rest of RAG Pipeline) ...