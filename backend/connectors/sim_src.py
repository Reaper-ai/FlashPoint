import pathway as pw
import json
import time
import os
from utils.logger import logger

class SimulationSource(pw.io.InputConnector):
    """
    Reads a JSONL file line-by-line with a delay to mimic a live stream.
    Updates the timestamp to current time so the AI treats it as 'Fresh'.
    """
    
    def __init__(self, file_path, interval=5):
        # interval = seconds between events (set to 5 for a fast demo)
        self.file_path = file_path
        self.interval = interval

    def read(self):
        # Check if file exists
        if not os.path.exists(self.file_path):
            logger.warning(f"⚠️ Simulation file not found: {self.file_path}")
            return

        logger.info(f"Starting Simulation Stream from {self.file_path}...")
        
        with open(self.file_path, "r") as f:
            for line in f:
                if line.strip():
                    try:
                        data = json.loads(line)
                        
                        # CRITICAL: Overwrite timestamp to NOW
                        # This ensures the AI thinks the event just happened.
                        data["timestamp"] = time.time()
                        
                        yield data
                        
                        # Sleep to simulate "Live Reporting" cadence
                        time.sleep(self.interval)
                        
                    except json.JSONDecodeError:
                        continue
        
        logger.info("✅ Simulation Stream Finished.")