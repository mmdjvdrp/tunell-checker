import os
import asyncio
from aiohttp import web
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# دریافت اطلاعات از سرور رندر
API_ID = int(os.environ.get('API_ID', 2040))
API_HASH = os.environ.get('API_HASH', 'b18441a1ff607e10a989891a5462e627')
SESSION_STRING = os.environ.get('SESSION_STRING', '')

SOURCE_CHANNEL = os.environ.get('SOURCE_CHANNEL', '')
TARGET_BOT = os.environ.get('TARGET_BOT', '')

# تابع تبدیل آیدی‌های عددی به int (تلتون آیدی عددی را به صورت int می‌خواهد)
def parse_chat_id(chat_id_str):
    if not chat_id_str:
        return ""
    val = str(chat_id_str).strip()
    # اگر آیدی عددی بود (چه مثبت چه منفی مثل -100...) آن را به عدد تبدیل کن
    if val.lstrip('-').isdigit():
        return int(val)
    return val

SOURCE_CHANNEL = parse_chat_id(SOURCE_CHANNEL)
TARGET_BOT = parse_chat_id(TARGET_BOT)

# تنظیم کلاینت تلگرام
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

# ==========================================
# بخش فیلتر و فوروارد پیام‌ها
# ==========================================
BLACKLIST_KEYWORDS = ["boost", "premium", "active"]

# گوش دادن به پیام‌های جدید از کانال مبدا
@client.on(events.NewMessage(chats=SOURCE_CHANNEL))
async def filter_and_forward_handler(event):
    msg_text = event.message.text or ""
    text_lower = msg_text.lower()
    
    # بررسی اینکه آیا کلمات ممنوعه در متن وجود دارند یا خیر
    has_restriction = any(keyword in text_lower for keyword in BLACKLIST_KEYWORDS)
    
    if has_restriction:
        print(f"🚫 پیام رد شد (دارای کلمات ممنوعه: boost/premium/active)")
        return
        
    # اگر کلمات ممنوعه را نداشت، متن پیام به ربات مقصد ارسال می‌شود
    try:
        await client.send_message(TARGET_BOT, msg_text)
        print("✅ پیام تایید و با موفقیت به ربات ارسال شد!")
    except Exception as e:
        print(f"❌ خطا در ارسال پیام به ربات: {e}")

# ==========================================
# بخش وب سرور رندر و اجرای اصلی
# ==========================================
async def handle(request):
    """جلوگیری از خاموش شدن سرور رندر"""
    return web.Response(text="Filter Bot is running successfully!")

async def main():
    # راه‌اندازی وب‌سرور aiohttp
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.environ.get('PORT', 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"✅ وب‌سرور روی پورت {port} اجرا شد.")
    
    # استارت کردن یوزربات
    await client.start()
    print("✅ یوزربات متصل شد! در حال رصد کانال هدایا...")
    
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
