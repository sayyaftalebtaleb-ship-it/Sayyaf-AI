import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from g4f.client import Client
import nest_asyncio

# حل مشكلة تشغيل الـ Loop في السيرفرات السحابية
nest_asyncio.apply()

logging.basicConfig(level=logging.INFO)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # التأكد من وجود نص في الرسالة
    if not update.message.text:
        return

    user_text = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        # استخدام مكتبة g4f للوصول لذكاء اصطناعي مجاني
        client = Client()
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": user_text}],
        )
        answer = response.choices[0].message.content
        await update.message.reply_text(answer)
    except Exception as e:
        print(f"Error: {e}")
        await update.message.reply_text("عذراً، النظام مشغول قليلاً. أعد المحاولة بعد لحظات.")

if __name__ == '__main__':
    # ضع التوكن الذي حصلت عليه من BotFather هنا بين علامتي التنصيص
    TOKEN = '7965345356:AAEiY2Q3UQ6WZvpFQAAmap0eebvLRvWXVuY'
    
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("البوت انطلق!")
    application.run_polling()
