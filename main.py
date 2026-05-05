import os, asyncio, g4f
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# 1. خادم ويب بسيط
app = Flask(__name__)
@app.route('/')
def home(): return "Bot Status: Online", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# 2. وظيفة جلب الرد مع تجربة عدة موفرين (Providers)
async def get_ai_response(text):
    # قائمة بأفضل الموفرين حالياً
    test_providers = [
        g4f.Provider.Blackbox,
        g4f.Provider.ChatGptEs,
        g4f.Provider.DuckDuckGo,
        g4f.Provider.ChatGpt,
        g4f.Provider.Liaobots
    ]
    
    for provider in test_providers:
        try:
            response = await g4f.ChatCompletion.create_async(
                model=g4f.models.default,
                messages=[{"role": "user", "content": text}],
                provider=provider
            )
            if response and len(str(response)) > 2:
                return response
        except Exception as e:
            print(f"فشل الموفر {provider.__name__}: {e}")
            continue
    return None

# 3. معالج الرسائل
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    answer = await get_ai_response(update.message.text)
    
    if answer:
        await update.message.reply_text(answer)
    else:
        await update.message.reply_text("عذراً، جميع محركات الذكاء الاصطناعي لا تستجيب حالياً. حاول مجدداً بعد دقيقة.")

# 4. التشغيل
if __name__ == '__main__':
    Thread(target=run_flask).start()
    
    # استبدل TOKEN_HERE بتوكن بوتك الجديد
    TOKEN = "8665085128:AAF_lrCk-Kvn3fhf9N17pP6zwq0T_CNFL_8"
    
    # تشغيل البوت مع مسح أي رسائل قديمة عالقة (drop_pending_updates)
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("Bot is starting...")
    application.run_polling(drop_pending_updates=True)
