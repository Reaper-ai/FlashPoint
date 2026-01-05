import os
import asyncio
import pathway as pw
from datetime import datetime
from telethon import TelegramClient, events
from dotenv import load_dotenv

# 1. Load Environment Variables
load_dotenv()

API_ID = os.getenv("TELEGRAM_API_ID")
API_HASH = os.getenv("TELEGRAM_API_HASH")
PHONE = os.getenv("TELEGRAM_PHONE")
CHANNELS = ["intelslava", "insider_paper", "disclosetv"]

class TelegramSource(pw.io.python.ConnectorSubject):
    def run(self):
        """
        Main entry point for Pathway.
        """
        # 2. Setup Async Loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # 3. Initialize Client
        # IMPORTANT: We use 'session_flashpoint' to match the file you just created.
        client = TelegramClient('session_flashpoint', API_ID, API_HASH)

        # 4. Define Handler (For Live Data)
        @client.on(events.NewMessage(chats=CHANNELS))
        async def handler(event):
            await self._process_message(event, "LIVE")

        # 5. Define Main Logic
        async def main_sequence():
            print(f"🔌 [Telegram] Connecting using saved session for {PHONE}...")
            
            # Because you already logged in, this will verify the session file 
            # and connect IMMEDIATELY without asking for code/phone.
            await client.start(phone=PHONE)
            
            print("✅ [Telegram] CONNECTED! (Session Valid)")

            # --- FETCH REAL HISTORY ---
            print("📜 [Telegram] Fetching last 3 messages per channel...")
            for channel in CHANNELS:
                try:
                    # Get last 3 messages from real history
                    async for message in client.iter_messages(channel, limit=3):
                        if message and message.text:
                            await self._process_message(message, "HISTORY")
                except Exception as e:
                    print(f"⚠️ [Telegram] Error reading {channel}: {e}")

            # --- LISTEN FOREVER ---
            print("👀 [Telegram] History loaded. Listening for new breaking news...")
            await client.run_until_disconnected()

        # 6. Run Execution
        try:
            loop.run_until_complete(main_sequence())
        except KeyboardInterrupt:
            pass

    async def _process_message(self, event, tag):
        """Helper to format data for Pathway"""
        sender = await event.get_sender()
        username = sender.username if sender else "Unknown"
        
        # Clean text for console preview
        text_clean = str(event.text).replace('\n', ' ')[:60]

        row = {
            "source": "telegram",
            "author": str(username),
            "text": str(event.text),
            "url": f"https://t.me/{username}/{event.id}",
            "raw_timestamp": float(event.date.timestamp()),
            "ingested_at": datetime.now().isoformat()
        }
        
        # Push to Pathway Engine
        self.next(**row)
        print(f"⚡ [{tag}] {username}: {text_clean}...", flush=True)