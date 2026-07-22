import os
import sys
import asyncio

# --- رفع خطای ناسازگاری asyncio ---
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

import traceback
import threading
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer

try:
    from pyrogram import Client, filters
    from pyrogram.types import Message
except ImportError as e:
    print(f"خطا در لود کتابخانه‌ها: {e}")
    sys.exit(1)


# --- وب‌سرور سبک ---
def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    class QuietHandler(SimpleHTTPRequestHandler):
        def log_message(self, format, *args):
            pass
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"Userbot is alive and running!")

    try:
        server = TCPServer(("0.0.0.0", port), QuietHandler)
        print(f"Web server successfully started on port {port}")
        server.serve_forever()
    except Exception as e:
        print(f"Web server failed to start: {e}")

threading.Thread(target=run_web_server, daemon=True).start()


# --- لود متغیرهای محیطی و اجرای ایمن یوزربات ---
try:
    API_ID_ENV = os.environ.get("API_ID")
    API_HASH_ENV = os.environ.get("API_HASH")
    SESSION_STRING_ENV = os.environ.get("SESSION_STRING")
    SOURCE_CHANNEL_ENV = os.environ.get("SOURCE_CHANNEL")
    TARGET_BOT_ENV = os.environ.get("TARGET_BOT")

    if not all([API_ID_ENV, API_HASH_ENV, SESSION_STRING_ENV, SOURCE_CHANNEL_ENV, TARGET_BOT_ENV]):
        print("خطا: متغیرهای محیطی در تنظیمات رندر ست نشده‌اند!")
        sys.exit(1)

    API_ID = int(API_ID_ENV)
    # پاک‌سازی متغیرها از هرگونه کاراکتر اضافی، فاصله یا کوتیشن که معمولاً در کپی/پیست رخ می‌دهد
    API_HASH = API_HASH_ENV.strip("'\" \n\r\t")
    SESSION_STRING = SESSION_STRING_ENV.strip("'\" \n\r\t")

    def parse_chat_id(value):
        val = value.strip("'\" \n\r\t")
        if val.startswith("@"):
            return val
        if val.isdigit() or (val.startswith("-") and val[1:].isdigit()):
            return int(val)
        return val

    SOURCE_CHANNEL = parse_chat_id(SOURCE_CHANNEL_ENV)
    TARGET_BOT = parse_chat_id(TARGET_BOT_ENV)

    app = Client(
        "gift_filter_userbot",
        api_id=API_ID,
        api_hash=API_HASH,
        session_string=SESSION_STRING
    )

    BLACKLIST_KEYWORDS = ["boost", "premium", "active"]

    @app.on_message(filters.chat(SOURCE_CHANNEL) & filters.text)
    async def filter_and_forward(client: Client, message: Message):
        text_lower = message.text.lower()
        has_restriction = any(keyword in text_lower for keyword in BLACKLIST_KEYWORDS)
        
        if has_restriction:
            return
        
        try:
            await client.send_message(chat_id=TARGET_BOT, text=message.text)
            print(f"Message {message.id} forwarded successfully to {TARGET_BOT}")
        except Exception as e:
            print(f"Error forwarding message {message.id}: {e}")

    print("Userbot is starting now...")
    app.run()

except Exception as e:
    print("خطای غیرمنتظره در اجرای یوزربات رخ داد:")
    traceback.print_exc()
    sys.exit(1)
