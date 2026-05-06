import os, asyncio, httpx
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

app = Flask(__name__)
@app.route('/')
def home(): return "Sayyaf AI is Active", 200

user_memory = {}

async def get_ai_response(user_id, user_text, user_lang):
    if user_id not in user_memory:
        user_memory[user_id] = []
    
    dev_name = "سياف طالب" if user_lang != 'en' else "Sayyaf Taleb"
    
    system_prompt = (
        f"أنت Sayyaf AI. مطورك {dev_name}. "
        "لا تذكر هويتك إلا عند السؤال. "
        "نظم النصوص بجداول داخل (```) وقوائم واضحة."
    )

    # --- إعدادات الـ API ---
    # تأكد من وضع المفتاح بين علامتي التنصيص
    API_KEY = "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"
    API_URL = "[https://api.openai.com/v1/chat/completions](https://api.openai.com/v1/chat/completions)" 

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(user_memory[user_id][-6:])
    messages.append({"role": "user", "content": user_text})

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
            payload = {"model": "gpt-3.5-turbo", "messages": messages}
            
            response = await client.post(API_URL, json=payload, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                # التأكد من استخراج النص بشكل صحيح
                ai_reply = data['choices'][0]['message']['content']
                user_memory[user_id].append({"role": "user", "content": user_text})
                user_memory[user_id].append({"role": "assistant", "content": ai_reply})
                return ai_reply
            else:
                print(f"API Error: {response.text}") # يظهر لك في سجلات Render
                return None
        except Exception as e:
            print(f"Conn Error: {e}")
            return None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    user_text = update.message.text
    user_lang = update.effective_user.language_code

    # إصلاح وشم الكتابة
    stop_event = asyncio.Event()
    async def typing_loop():
        while not stop_event.is_set():
            try:
                await context.bot.send_chat_action(chat_id=chat_id, action="typing")
                await asyncio.sleep(4)
            except: break

    typing_task = asyncio.create_task(typing_loop())
    
    try:
        answer = await get_ai_response(user_id, user_text, user_lang)
        
        stop_event.set() # إيقاف الوشم
        await typing_task
        
        if answer:
            try:
                await update.message.reply_text(answer, parse_mode='Markdown')
            except:
                await update.message.reply_text(answer)
        else:
            # رسالة خطأ "مستترة" كما طلبت
            await update.message.reply_text("عذراً، حدث خطأ تقني في معالجة النص. أعد المحاولة لاحقاً.")
    except:
        stop_event.set()

if __name__ == '__main__':
    Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))).start()
    
    TOKEN = "7965345356:AAEiY2Q3UQ6WZvpFQAAmap0eebvLRvWXVuY"
    
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    application.run_polling(drop_pending_updates=True)
