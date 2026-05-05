import os
import asyncio
import logging
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
import g4f

# 1. إعداد Flask لإبقاء الخدمة Live على Render
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is Running Successfully!", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# 2. منطق جلب الرد من الذكاء الاصطناعي (محاولات متعددة)
async def get_ai_response(text):
    # قائمة بالمزودين الأكثر استقراراً حالياً
    providers = [
        g4f.Provider.Blackbox,
        g4f.Provider.ChatGptEs,
        g4f.Provider.DuckDuckGo,
        g4f.Provider.ChatGpt
    ]
    
    for provider in providers:
        try:
            response = await g4f.ChatCompletion.create_async(
                model=g4f.models.default,
                messages=[{"role": "user", "content": text}],
                provider=provider
            )
            if response and len(str(response)) > 5:
                return response
        except Exception as e:
            print(f"Provider {provider.__name__} failed: {e}")
            continue
    return None

# 3. معالج رسائل تليجرام
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    # إظهار حالة "جارٍ الكتابة"
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    response = await get_ai_response(update.message.text)
    
    if response:
        await update.message.reply_text(response)
    else:
        await update.message.reply_text("المعذرة يا صديقي، يبدو أن جميع المحركات مزدحمة الآن. حاول مرة أخرى بعد قليل.")

# 4. التشغيل الرئيسي
if __name__ == '__main__':
    # تشغيل خادم الويب في الخلفية
    Thread(target=run_flask).start()

    # --- ضع توكن البوت الخاص بك هنا ---
    TOKEN = "8665085128:AAF_lrCk-Kvn3fhf9N17pP6zwq0T_CNFL_8"

    # بناء التطبيق مع حل مشكلة الـ Conflict تلقائياً
    application = ApplicationBuilder().token(TOKEN).build()
    
    # إضافة معالج الرسائل
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("Bot is starting...")
    # استخدام سياق آمن للتشغيل لتجنب مشاكل الـ Event Loop في Render
    application.run_polling(drop_pending_updates=True)
