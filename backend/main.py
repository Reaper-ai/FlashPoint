import pathway as pw
from connectors.telegram_src import TelegramSource
from connectors.reddit_src import RedditSource

def run():
    print("🚀 Flashpoint Engine Starting (Multi-Source Mode)...")

    # 1. Define the Unified Schema
    class InputSchema(pw.Schema):
        source: str
        author: str
        text: str
        url: str
        raw_timestamp: float
        ingested_at: str

    # 2. Connect Telegram
    telegram_table = pw.io.python.read(
        TelegramSource(),
        schema=InputSchema,
        mode="streaming"
    )

    # 3. Connect Reddit
    reddit_table = pw.io.python.read(
        RedditSource(),
        schema=InputSchema,
        mode="streaming"
    )

    # --- THE FIX ---
    # We explicitly promise Pathway that Reddit and Telegram are separate streams.
    # This satisfies the "disjoint" requirement.
    reddit_table = reddit_table.promise_universes_are_disjoint(telegram_table)

    # 4. Now we can Concatenate safely
    unified_table = telegram_table.concat(reddit_table)

    # 5. Output to CSV (Backend Verification)
    pw.io.csv.write(unified_table, "output_unified.csv")

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