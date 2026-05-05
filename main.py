import os, requests, asyncio
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# 1. إعداد Flask (لضمان بقاء السيرفر Live)
app = Flask(__name__)
@app.route('/')
def home(): return "Sayyaf AI is Online and Ready!", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# 2. نظام الذاكرة الذكي
user_memory = {}

def get_ai_response(user_id, user_text, user_full_name):
    if user_id not in user_memory:
        user_memory[user_id] = []
    
    memory = user_memory[user_id]
    
    # التعليمات الثابتة (System Prompt) مع تصحيح اسمك
    system_prompt = (
        "اسمك Sayyaf AI. أنت مساعد ذكي، محترف، وصديق للمستخدم. "
        "مطورك هو المبرمج اليمني المبدع سياف طالب (Sayyaf Taleb). "
        "لا تذكر هويتك أو اسم مطورك إلا إذا سألك المستخدم عن ذلك مباشرة. "
        "يجب أن تكون إجاباتك منظمة جداً، استخدم العناوين والجداول والنقاط والـ Bold. "
        "كن ودوداً وتذكر تفاصيل الحوار السابقة مع المستخدم."
    )

    messages = [{"role": "system", "content": system_prompt}]
    for msg in memory:
        messages.append(msg)
    messages.append({"role": "user", "content": user_text})

    # استخدام الرابط المباشر لتجنب رسائل الـ Deprecation
    url = "https://text.pollinations.ai/"
    payload = {
        "messages": messages,
        "model": "openai",
        "private": True,
        "safe": True
    }

    try:
        response = requests.post(url, json=payload, timeout=60) # زيادة الوقت للردود الطويلة
        if response.status_code == 200:
            ai_reply = response.text
            # تحديث الذاكرة
            memory.append({"role": "user", "content": user_text})
            memory.append({"role": "assistant", "content": ai_reply})
            if len(memory) > 12: memory.pop(0); memory.pop(0) 
            return ai_reply
    except Exception as e:
        print(f"Error: {e}")
    return None

# 3. معالج الرسائل المحسن
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    
    user_id = update.effective_user.id
    user_text = update.message.text
    user_name = update.effective_user.full_name

    # إبقاء وشم "يكتب الآن" مستمراً بذكاء
    typing_task = asyncio.create_task(context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing"))
    
    # تنفيذ طلب الذكاء الاصطناعي
    loop = asyncio.get_event_loop()
    answer = await loop.run_in_executor(None, get_ai_response, user_id, user_text, user_name)
    
    if answer:
        await update.message.reply_text(answer, parse_mode='Markdown')
    else:
        await update.message.reply_text("عذراً يا صديقي، يبدو أن هناك ضغطاً على المحرك. حاول مرة أخرى.")

if __name__ == '__main__':
    Thread(target=run_flask).start()
    
    # --- هام جداً: ضع التوكن هنا ---
    TOKEN = "7965345356:AAEiY2Q3UQ6WZvpFQAAmap0eebvLRvWXVuY"

    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("Sayyaf AI is starting...")
    # حل مشكلة الـ Conflict نهائياً بمسح الرسائل القديمة
    application.run_polling(drop_pending_updates=True)
