import pathway as pw
import json
import time
import os

class SimulationSource(pw.io.python.ConnectorSubject):
    def __init__(self, file_path, interval=5):
        # 1. CRITICAL: Must initialize the parent class
        super().__init__()
        self.file_path = file_path
        self.interval = interval

    def run(self):
        # 2. Check path
        if not os.path.exists(self.file_path):
            print(f"❌ [Sim] File not found: {self.file_path}")
            return

        print(f"🚀 [Sim] Starting Simulation Loop from: {self.file_path}")
        
        # 3. Infinite Loop
        while True:
            try:
                with open(self.file_path, "r") as f:
                    lines = f.readlines()

                for line in lines:
                    if line.strip():
                        try:
                            data = json.loads(line)
                            
                            # Update timestamp to NOW
                            data["timestamp"] = time.time()
                            
                            # 4. Push data to Pathway engine
                            self.next(**data)
                            
                            print(f"🎭 [Sim] Injected: {data.get('text', '')[:30]}...")
                            time.sleep(self.interval)
                            
                        except json.JSONDecodeError:
                            continue
            except Exception as e:
                print(f"⚠️ [Sim] Read Error: {e}")
                time.sleep(1)