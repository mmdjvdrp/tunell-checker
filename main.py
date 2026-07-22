import os
import asyncio
import re
from aiohttp import web
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# دریافت اطلاعات از سرور رندر
API_ID = 2040
API_HASH = 'b18441a1ff607e10a989891a5462e627'
SESSION_STRING = os.environ.get('SESSION_STRING', '')

SOURCE_CHANNEL = os.environ.get('SOURCE_CHANNEL', '')
TARGET_BOT = os.environ.get('TARGET_BOT', '')

def parse_chat_id(chat_id_str):
    if not chat_id_str: return ""
    val = str(chat_id_str).strip()
    if val.lstrip('-').isdigit(): return int(val)
    return val

SOURCE_CHANNEL = parse_chat_id(SOURCE_CHANNEL)
TARGET_BOT = parse_chat_id(TARGET_BOT)

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

BLACKLIST_KEYWORDS = ["boost", "premium", "active"]

@client.on(events.NewMessage(chats=SOURCE_CHANNEL))
async def filter_and_extract_handler(event):
    msg_text = event.message.text or ""
    text_lower = msg_text.lower()
    
    # ۱. فیلتر کردن کلمات ممنوعه
    has_restriction = any(keyword in text_lower for keyword in BLACKLIST_KEYWORDS)
    if has_restriction:
        print("🚫 پیام دارای محدودیت بود و رد شد.")
        return

    # ۲. استخراج اطلاعات با Regex
    # پیدا کردن آیدی چنل‌ها (شروع با @)
    channels = re.findall(r'@[a-zA-Z0-9_]+', msg_text)
    
    # پیدا کردن لینک‌های داخل متن
    urls = re.findall(r'https?://[^\s\)]+', msg_text)
    
    # پیدا کردن لینک‌های دکمه‌های شیشه‌ای (در صورتی که بات شیشه‌ای داده باشد)
    if event.message.buttons:
        for row in event.message.buttons:
            for button in row:
                if hasattr(button, 'url') and button.url:
                    urls.append(button.url)
    
    # پیدا کردن پرچم‌ها (تشخیص یونیکد پرچم کشورها)
    flags = re.findall(r'[\U0001F1E6-\U0001F1FF]{2}', msg_text)

    # حذف موارد تکراری
    channels = list(dict.fromkeys(channels))
    urls = list(dict.fromkeys(urls))
    flags = list(dict.fromkeys(flags))

    # ۳. ساخت پیام مرتب و تمیز
    extracted_text = "🎁 گیفت واجد شرایط پیدا شد!\n\n"
    
    if channels:
        extracted_text += "📢 چنل‌ها:\n" + "\n".join(channels) + "\n\n"
        
    if flags:
        extracted_text += f"🏳️ پرچم‌ها: {' '.join(flags)}\n\n"
        
    if urls:
        extracted_text += "🔗 لینک‌ها:\n" + "\n".join(urls)
        
    # در صورتی که هیچ لینکی و چنلی پیدا نکرد (محض احتیاط)
    if not channels and not urls:
        extracted_text += f"متن (خلاصه):\n{msg_text[:300]}"

    # ۴. ارسال به ربات مقصد
    try:
        await client.send_message(TARGET_BOT, extracted_text)
        print("✅ اطلاعات استخراج شد و به ربات ارسال شد!")
    except Exception as e:
        print(f"❌ خطا در ارسال به ربات: {e}")

# ==========================================
# بخش وب سرور رندر و اجرای اصلی
# ==========================================
async def handle(request):
    return web.Response(text="Smart Extractor Bot is running!")

async def main():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.environ.get('PORT', 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    await client.start()
    print("✅ یوزربات هوشمند متصل شد و منتظر گیفت‌هاست...")
    
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
