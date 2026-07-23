import os
import asyncio
import re
from aiohttp import web
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# کلیدهای اصلی تلگرام
API_ID = 2040
API_HASH = 'b18441a1ff607e10a989891a5462e627'

# دریافت متغیرهای قبلی از سرور رندر
SESSION_STRING = os.environ.get('SESSION_STRING', '')
SOURCE_CHANNEL = os.environ.get('SOURCE_CHANNEL', '')
TARGET_BOT = os.environ.get('TARGET_BOT', '')
SECOND_CHANNEL = os.environ.get('SECOND_CHANNEL', '')

# ==========================================
# اطلاعات کانال‌ها و ربات جدید (مستقیم در کد)
# ==========================================
NEW_CHANNELS = ["@ton_drops_me_stars", "@ton_drops_me_giveaway"]
NEW_TARGET_BOT = "@giveawaycheckerbot"

def parse_chat_id(chat_id_str):
    if not chat_id_str: return ""
    val = str(chat_id_str).strip()
    if val.lstrip('-').isdigit(): return int(val)
    return val

SOURCE_CHANNEL = parse_chat_id(SOURCE_CHANNEL)
TARGET_BOT = parse_chat_id(TARGET_BOT)
SECOND_CHANNEL = parse_chat_id(SECOND_CHANNEL)

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

BLACKLIST_KEYWORDS = ["boost", "premium", "active"]

# ==========================================
# ۱. هندلر کانال اول (فیلتر و استخراج گیفت‌ها -> ارسال به ربات اول)
# ==========================================
if SOURCE_CHANNEL:
    @client.on(events.NewMessage(chats=SOURCE_CHANNEL))
    async def filter_and_extract_handler(event):
        msg_text = event.message.text or ""
        text_lower = msg_text.lower()
        
        has_restriction = any(keyword in text_lower for keyword in BLACKLIST_KEYWORDS)
        if has_restriction:
            return

        channels = re.findall(r'@[a-zA-Z0-9_]+', msg_text)
        urls = re.findall(r'https?://[^\s\)]+', msg_text)
        
        if event.message.buttons:
            for row in event.message.buttons:
                for button in row:
                    if hasattr(button, 'url') and button.url:
                        urls.append(button.url)
        
        flags = re.findall(r'[\U0001F1E6-\U0001F1FF]{2}', msg_text)

        channels = list(dict.fromkeys(channels))
        urls = list(dict.fromkeys(urls))
        flags = list(dict.fromkeys(flags))

        extracted_text = "🎁 **گیفت واجد شرایط پیدا شد!**\n\n"
        if channels: extracted_text += "📢 چنل‌ها:\n" + "\n".join(channels) + "\n\n"
        if flags: extracted_text += f"🏳️ پرچم‌ها: {' '.join(flags)}\n\n"
        if urls: extracted_text += "🔗 لینک‌ها:\n" + "\n".join(urls)
            
        if not channels and not urls:
            extracted_text += f"متن:\n{msg_text[:300]}"

        try:
            await client.send_message(TARGET_BOT, extracted_text)
        except Exception as e:
            print(f"❌ خطا کانال اول: {e}")

# ==========================================
# ۲. هندلر کانال دوم (ارسال همه پیام‌ها -> به ربات اول)
# ==========================================
if SECOND_CHANNEL:
    @client.on(events.NewMessage(chats=SECOND_CHANNEL))
    async def forward_all_handler(event):
        msg_text = event.message.text or "پیام تصویری/ویدیویی بدون متن"
        safe_text = msg_text.replace('*', '').replace('_', '').replace('[', '').replace(']', '')
        final_text = f"📩 **پیام جدید از کانال دوم:**\n\n{safe_text}"
        
        try:
            await client.send_message(TARGET_BOT, final_text)
        except Exception as e:
            print(f"❌ خطا در ارسال کانال دوم: {e}")

# ==========================================
# ۳. هندلر کانال‌های جدید استارز (ارسال -> به ربات دوم: giveawaycheckerbot)
# ==========================================
@client.on(events.NewMessage(chats=NEW_CHANNELS))
async def new_stars_giveaway_handler(event):
    msg_text = event.message.text or ""
    
    # برای جلوگیری از ارور مارک‌دان در ربات‌ها، کاراکترهای خاص رو پاک می‌کنیم
    safe_text = msg_text.replace('*', '').replace('_', '').replace('[', '').replace(']', '')
    
    try:
        # ارسال پیام‌های این دو کانال به ربات giveawaycheckerbot
        await client.send_message(NEW_TARGET_BOT, safe_text)
        print("✅ پیام جدید از کانال‌های استارز به ربات چکر ارسال شد!")
    except Exception as e:
        print(f"❌ خطا در ارسال به ربات چکر: {e}")

# ==========================================
# بخش وب سرور رندر و اجرای اصلی
# ==========================================
async def handle(request):
    return web.Response(text="Multi-Bot Extractor is running successfully!")

async def main():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.environ.get('PORT', 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    await client.start()
    print("✅ یوزربات متصل شد! در حال رصد تمامی کانال‌ها و ارسال به ربات‌های مربوطه...")
    
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
