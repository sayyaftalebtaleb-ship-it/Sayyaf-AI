import os, asyncio, requests
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

app = Flask(__name__)
@app.route('/')
def home(): return "Sayyaf AI is Online", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

user_memory = {}

def fetch_ai_reply(user_id, user_text, user_lang):
    if user_id not in user_memory:
        user_memory[user_id] = []
    
    dev_name = "سياف طالب" if user_lang != 'en' else "Sayyaf Taleb"
    
    system_prompt = (
        f"أنت مساعد ذكي محترف اسمك Sayyaf AI ومطورك هو {dev_name}. "
        "لا تذكر اسمك إلا إذا سُئلت. "
        "ضع الجداول داخل كود بلوك (```) لضمان التنسيق."
    )

    messages = [{"role": "system", "content": system_prompt}]
    # قللنا الذاكرة لآخر 4 رسائل فقط لتخفيف الضغط على المحرك وتجنب الرفض
    messages.extend(user_memory[user_id][-4:]) 
    messages.append({"role": "user", "content": user_text})

    # الرابط الأساسي المباشر الذي يعطي النص مباشرة
    url = "[https://text.pollinations.ai/](https://text.pollinations.ai/)"
    
    try:
        # إضافة User-Agent لكي لا يظن المحرك أن الطلب قادم من "روبوت اختراق" ويرفضه
        headers = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
        payload = {"messages": messages, "model": "openai", "private": True}
        
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        
        if response.status_code == 200:
            ai_reply = response.text
            user_memory[user_id].append({"role": "user", "content": user_text})
            user_memory[user_id].append({"role": "assistant", "content": ai_reply})
            return ai_reply
        else:
            # هنا التعديل الذهبي: البوت سيرسل لك سبب رفض السيرفر!
            return f"⚠️ **خطأ من السيرفر:**\nرمز الخطأ: `{response.status_code}`\nتفاصيل: {response.text}"
            
    except Exception as e:
        # وإذا كان الخطأ من الاتصال، سيرسل لك نوع الخطأ!
        return f"⚠️ **خطأ في الاتصال بالمحرك:**\n`{str(e)}`"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    user_text = update.message.text
    user_lang = update.effective_user.language_code

    stop_typing = asyncio.Event()
    async def keep_typing():
        while not stop_typing.is_set():
            try:
                await context.bot.send_chat_action(chat_id=chat_id, action="typing")
                await asyncio.sleep(3.5)
            except: break

    typing_task = asyncio.create_task(keep_typing())
    
    try:
        loop = asyncio.get_event_loop()
        answer = await loop.run_in_executor(None, fetch_ai_reply, user_id, user_text, user_lang)
        
        stop_typing.set()
        await typing_task
        
        if answer:
            try:
                await update.message.reply_text(answer, parse_mode='Markdown')
            except:
                await update.message.reply_text(answer)
        else:
            await update.message.reply_text("عذراً، لم أتمكن من الحصول على الرد.")
    except Exception as e:
        stop_typing.set()
        await update.message.reply_text(f"⚠️ خطأ داخلي في البوت:\n`{str(e)}`")

if __name__ == '__main__':
    Thread(target=run_flask).start()
    
    # ⚠️ لا تنسَ وضع التوكن الخاص بك
    TOKEN = "7965345356:AAEiY2Q3UQ6WZvpFQAAmap0eebvLRvWXVuY"
    
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    application.run_polling(drop_pending_updates=True)
