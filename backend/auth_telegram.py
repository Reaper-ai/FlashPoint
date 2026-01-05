import os
import sys
from telethon import TelegramClient

# 1. Manually check for variables injected by Docker
api_id = os.getenv("TELEGRAM_API_ID")
api_hash = os.getenv("TELEGRAM_API_HASH")
phone = os.getenv("TELEGRAM_PHONE")

print(f"DEBUG: Found Phone Number: {phone}")

if not api_id or not api_hash or not phone:
    print("❌ ERROR: Keys are missing from .env file!")
    sys.exit(1)

def interactive_login():
    print("🔒 STARTING LOGIN...")
    print("---------------------")
    
    # 2. Create the Client
    client = TelegramClient('session_flashpoint', api_id, api_hash)
    
    async def main():
        # 3. Connect (Passing phone here skips the phone prompt)
        print(f"📲 Sending login code to: {phone}")
        print("   (Check your Telegram APP, not SMS)")
        
        await client.start(phone=phone)
        
        print("\n✅ LOGIN SUCCESSFUL!")
        print("✅ 'session_flashpoint.session' saved successfully.")
        print("---------------------")
        print("🚀 YOU CAN NOW RUN THE MAIN DOCKER COMMAND.")

    with client:
        client.loop.run_until_complete(main())

if __name__ == "__main__":
    interactive_login()