"""Telegram Session Authentication Setup

One-time authentication script to create a persistent Telegram session.

Flow:
1. Load Telegram API credentials from .env
2. Create TelegramClient with session file
3. Authenticate via phone code (manual step)
4. Save session file for subsequent use

Note: Run this once per environment. Session file persists across restarts.
"""

import os
import sys
from telethon import TelegramClient
from dotenv import load_dotenv

# Load Telegram API credentials from environment
load_dotenv()  # Load variables from .env88
api_id = os.getenv("TELEGRAM_API_ID")
api_hash = os.getenv("TELEGRAM_API_HASH")
phone = os.getenv("TELEGRAM_PHONE")

print(f"DEBUG: Found Phone Number: {phone}")

# Validate that all required credentials are present
if not api_id or not api_hash or not phone:
    print("❌ ERROR: Keys are missing from .env file!")
    sys.exit(1)

def interactive_login():
    """Perform interactive Telegram authentication
    
    Flow:
    1. Create Telethon client with API credentials
    2. Connect and request authentication code
    3. User receives code via Telegram app (not SMS)
    4. Session file saved for future use
    
    Output:
    - Creates 'session_flashpoint.session' file in working directory
    - Ready for automated connector startup
    """
    print("🔒 STARTING LOGIN...")
    print("---------------------")
    
    # Create TelegramClient instance with persistent session file
    client = TelegramClient('session_flashpoint', api_id, api_hash)
    
    async def main():
        """Async authentication sequence"""
        # Initiate connection and send code
        print(f"📲 Sending login code to: {phone}")
        print("   (Check your Telegram APP, not SMS)")
        
        # Start session: prompts for code in Telegram app
        await client.start(phone=phone)
        
        print("\n✅ LOGIN SUCCESSFUL!")
        print("✅ 'session_flashpoint.session' saved successfully.")
        print("---------------------")
        print("🚀 YOU CAN NOW RUN THE MAIN DOCKER COMMAND.")

    # Execute async auth flow
    with client:
        client.loop.run_until_complete(main())

if __name__ == "__main__":
    """Entry point: Run interactive authentication"""
    interactive_login()