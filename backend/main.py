# from connectors.sim_src import SimulationSource
# from connectors.news_src import NewsSource, RssSource
import pathway as pw
from connectors.telegram_src import TelegramSource  # Import the Class

def run():
    print("🚀 Flashpoint Engine Starting...")

    class InputSchema(pw.Schema):
        source: str
        author: str
        text: str
        url: str
        raw_timestamp: float
        ingested_at: str

    # --- THE FIX ---
    # Instantiate the class: TelegramSource()
    # This creates the object Pathway expects.
    telegram_table = pw.io.python.read(
        TelegramSource(), 
        schema=InputSchema,
        mode="streaming"
    )

    pw.io.csv.write(telegram_table, "output_telegram.csv")

    print("✅ Pipeline configured.")
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