import os
import asyncio
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
import g4f

# إعداد Flask للـ Render
app = Flask(__name__)
@app.route('/')
def home(): return "Bot is Live!", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# دالة الرد الذكية
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        # محاولة جلب الرد باستخدام أكثر من موفر لضمان العمل
        response = await g4f.ChatCompletion.create_async(
            model=g4f.models.default,
            messages=[{"role": "user", "content": update.message.text}],
            provider=g4f.Provider.ChatGptEs # موفر مستقر غالباً
        )
        
        if response and len(response) > 0:
            await update.message.reply_text(response)
        else:
            raise Exception("Empty response")
            
    except Exception:
        try:
            # محاولة ثانية بموفر احتياطي (Bing أو غيره تلقائياً)
            response = await g4f.ChatCompletion.create_async(
                model=g4f.models.gpt_35_turbo,
                messages=[{"role": "user", "content": update.message.text}]
            )
            await update.message.reply_text(response)
        except Exception as final_error:
            print(f"Final Error: {final_error}")
            await update.message.reply_text("المعذرة، جميع المحركات مزدحمة حالياً، أعد المحاولة بعد قليل.")

if __name__ == '__main__':
    Thread(target=run_flask).start()
    
    # ضع التوكن الخاص بك هنا
    TOKEN = "7965345356:AAEiY2Q3UQ6WZvpFQAAmap0eebvLRvWXVuY"
    
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    application.run_polling()
