import os
import logging
import asyncio
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
import g4f

# 1. خادم ويب بسيط لإبقاء الخدمة تعمل على Render
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Bot is Running!", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# 2. منطق الرد على الرسائل باستخدام الذكاء الاصطناعي
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user_text = update.message.text
    try:
        # إظهار حالة "جارٍ الكتابة" في تليجرام
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        # محاولة جلب رد من الذكاء الاصطناعي
        response = await g4f.ChatCompletion.create_async(
            model=g4f.models.gpt_35_turbo,
            messages=[{"role": "user", "content": user_text}],
        )
        
        if response:
            await update.message.reply_text(response)
        else:
            await update.message.reply_text("المعذرة، المحرك لا يستجيب حالياً، جرب إرسال الرسالة مرة أخرى.")

    except Exception as e:
        print(f"Error details: {e}")
        await update.message.reply_text("عذراً، واجهت مشكلة في معالجة طلبك، سأحاول تحسين الاتصال.")

# 3. تشغيل البوت والخادم معاً
if __name__ == '__main__':
    # تشغيل Flask في خيط منفصل
    Thread(target=run_flask).start()

    # --- ضع التوكن الخاص بك هنا بدقة ---
    TOKEN = "7965345356:AAEiY2Q3UQ6WZvpFQAAmap0eebvLRvWXVuY" 

    # بناء تطبيق تليجرام
    application = ApplicationBuilder().token(TOKEN).build()
    
    # إضافة معالج الرسائل النصية
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("Starting Telegram Bot...")
    application.run_polling()
