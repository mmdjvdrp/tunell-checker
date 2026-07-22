import os
import threading
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
from pyrogram import Client, filters
from pyrogram.types import Message

# --- وب‌سرور سبک برای راضی نگه داشتن پورت رندر (مخصوص پلن رایگان) ---
def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    class QuietHandler(SimpleHTTPRequestHandler):
        def log_message(self, format, *args):
            pass  # غیرفعال کردن لاگ‌های اضافی در کنسول رندر
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

# اجرای وب‌سرور در یک بخش (Thread) مجزا در پس‌زمینه
threading.Thread(target=run_web_server, daemon=True).start()


# --- دریافت تنظیمات از متغیرهای محیطی (Environment Variables) ---
API_ID_ENV = os.environ.get("API_ID")
API_HASH = os.environ.get("API_HASH")
SESSION_STRING = os.environ.get("SESSION_STRING")
SOURCE_CHANNEL_ENV = os.environ.get("SOURCE_CHANNEL")
TARGET_BOT_ENV = os.environ.get("TARGET_BOT")

# بررسی اینکه تمام متغیرها در رندر وارد شده باشند
if not all([API_ID_ENV, API_HASH, SESSION_STRING, SOURCE_CHANNEL_ENV, TARGET_BOT_ENV]):
    raise ValueError(
        "خطا: متغیرهای محیطی در رندر به درستی تنظیم نشده‌اند! "
        "لطفاً مطمئن شوید API_ID, API_HASH, SESSION_STRING, SOURCE_CHANNEL, TARGET_BOT تعریف شده باشند."
    )

API_ID = int(API_ID_ENV)

# تابعی برای تبدیل آیدی‌ها به عدد (اگر آیدی عددی کانال وارد شده باشد)
def parse_chat_id(value):
    val = value.strip()
    if val.startswith("@"):
        return val
    if val.isdigit() or (val.startswith("-") and val[1:].isdigit()):
        return int(val)
    return val

SOURCE_CHANNEL = parse_chat_id(SOURCE_CHANNEL_ENV)
TARGET_BOT = parse_chat_id(TARGET_BOT_ENV)


# --- راه‌اندازی کلاینت پایروگرام با استفاده از رشته نشست ---
app = Client(
    "gift_filter_userbot",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION_STRING
)

# لیست کلمات کلیدی برای حذف پیام‌هایی که محدودیت بوست، پریمیوم یا اکتیو دارند
BLACKLIST_KEYWORDS = ["boost", "premium", "active"]


@app.on_message(filters.chat(SOURCE_CHANNEL) & filters.text)
async def filter_and_forward(client: Client, message: Message):
    text_lower = message.text.lower()
    
    # بررسی شرایط فیلتر
    has_restriction = any(keyword in text_lower for keyword in BLACKLIST_KEYWORDS)
    
    if has_restriction:
        print(f"پیام شماره {message.id} به دلیل داشتن کلمات فیلتر شده رد شد.")
        return
    
    try:
        # فرستادن متن پیام به ربات مقصد
        await client.send_message(chat_id=TARGET_BOT, text=message.text)
        print(f"پیام شماره {message.id} با موفقیت به ربات {TARGET_BOT} فرستاده شد.")
    except Exception as e:
        print(f"خطا در فرستادن پیام: {e}")


if __name__ == "__main__":
    print("Userbot is running...")
    app.run()
