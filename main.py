import os, asyncio, g4f
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters

app = Flask(__name__)
@app.route('/')
def home(): return "OK", 200

async def handle(update, context):
    if not update.message.text: return
    # إشعار الكتابة
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        res = await g4f.ChatCompletion.create_async(
            model=g4f.models.gpt_4, # جربنا نغير الموديل لـ 4
            messages=[{"role": "user", "content": update.message.text}],
            provider=g4f.Provider.Blackbox
        )
        await update.message.reply_text(res if res else "لم أستطع جلب رد.")
    except:
        await update.message.reply_text("مشكلة فنية، حاول مجدداً.")

if __name__ == '__main__':
    Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))).start()
    # تأكد من وضع التوكن الجديد هنا
    app_tg = ApplicationBuilder().token("8665085128:AAF_lrCk-Kvn3fhf9N17pP6zwq0T_CNFL_8").build()
    app_tg.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle))
    # drop_pending_updates هو اللي بيمسح الرسائل القديمة اللي معلقة البوت
    app_tg.run_polling(drop_pending_updates=True)
