from connectors.sim_src import SimulationSource
from connectors.news_src import NewsSource, RssSource
import pathway as pw

God_Mode = False  # Set to True to enable simulation source

def run():
    # Schema definition ...
    schema = {
        "text": str,
        "source": str,
        "url": str,
        "timestamp": float,
        "bias_tag": str
    }



    # 1. News API Sources (12 hr delay free quota)
    t_news = pw.io.python.read(
        NewsSource("YOUR_GNEWS_API_KEY", query="crisis OR war OR military"),
        schema=schema
    )

    # 2. RSS Feeds from State Media + Western Media
    t_rss_russia = pw.io.python.read(
        RssSource("https://sputnikglobe.com/export/rss2/archive/index.xml", bias_tag="State-Media (RU)"),
        schema=schema
    )

    t_rss_china = pw.io.python.read(
        RssSource("https://www.cgtn.com/subscribe/rss/section/world.xml", bias_tag="State-Media (CN)"),
        schema=schema
    )

    t_rss_us = pw.io.python.read(
        RssSource("https://rss.nytimes.com/services/xml/rss/nyt/World.xml", bias_tag="US/Western"),
        schema=schema
    )

    t_rss_uk = pw.io.python.read(
        RssSource("https://feeds.bbci.co.uk/news/world/rss.xml", bias_tag="UK/Western"),
        schema=schema
    )

    t_rss_combined = t_rss_russia + t_rss_china + t_rss_us + t_rss_uk    
    # 3. reddit source 



    # 4. telegram source



    # 5. Simulation Source (The "God Mode" Stream)
    # Pointing to the file you created in Step 1


    combined_stream = t_news + t_rss_combined

    if (God_Mode):
        t_sim = pw.io.python.read(
            SimulationSource("data/crisis_scenario.jsonl", interval=10),
            schema=schema
        )

        combined_stream = combined_stream + t_sim

    
    # ... (Rest of RAG Pipeline) ...