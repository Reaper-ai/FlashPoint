"""Simulation Data Source for FlashPoint - Test/Demo Mode

Loads and streams events from a JSONL file for development and testing.

Use cases:
- Test pipeline without external API dependencies
- Reproduce scenarios for debugging
- Load testing and performance validation
- Demo mode with controlled data flow

Each line in the JSONL file is treated as an event (must match InputSchema).
"""

import pathway as pw
import json
import time
import os

class SimulationSource(pw.io.python.ConnectorSubject):
    """Simulation connector: reads JSONL file and emits events at controlled rate"""
    
    def __init__(self, file_path, interval=5):
        """Initialize simulation source
        
        Args:
            file_path (str): Path to JSONL file with test events
            interval (int): Delay in seconds between event emissions
        """
        # 1. CRITICAL: Must initialize the parent class
        super().__init__()
        self.file_path = file_path
        self.interval = interval

    def run(self):
        """Main execution loop: read JSONL file and stream events
        
        Process:
        1. Load entire file into memory
        2. Parse each JSON line
        3. Update timestamp to current time
        4. Emit to Pathway
        5. Sleep between events
        6. Repeat infinitely
        """
        # ========== FILE VALIDATION ==========
        # 2. Check path exists
        if not os.path.exists(self.file_path):
            print(f"❌ [Sim] File not found: {self.file_path}")
            return

        print(f"🚀 [Sim] Starting Simulation Loop from: {self.file_path}")
        
        # ========== MAIN LOOP ==========
        # 3. Infinite Loop (restart from beginning when EOF reached)
        while True:
            try:
                # Read entire file
                with open(self.file_path, "r") as f:
                    lines = f.readlines()

                # ========== PROCESS EACH LINE ==========
                for line in lines:
                    if line.strip():  # Skip empty lines
                        try:
                            # Parse JSON line
                            data = json.loads(line)
                            
                            # ========== TIMESTAMP INJECTION ==========
                            # Update timestamp to NOW (not historical)
                            data["timestamp"] = time.time()
                            
                            # ========== EMIT TO PATHWAY ==========
                            # 4. Push data to Pathway engine
                            self.next(**data)
                            
                            # Log injection
                            print(f"🎭 [Sim] Injected: {data.get('text', '')[:30]}...")
                            
                            # ========== FLOW CONTROL ==========
                            # Sleep between events (configurable rate)
                            time.sleep(self.interval)
                            
                        except json.JSONDecodeError:
                            # Skip malformed lines
                            continue
                            
            except Exception as e:
                # Handle file read errors
                print(f"⚠️ [Sim] Read Error: {e}")
                time.sleep(1)
                # Will retry reading the file