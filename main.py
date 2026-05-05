import os, requests, asyncio
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

app = Flask(__name__)
@app.route('/')
def home(): return "Sayyaf AI is Online", 200

# مخزن للذاكرة (سيحفظ الرسائل لكل مستخدم بشكل منفصل)
user_memory = {}

def get_ai_response(user_id, user_text):
    # إدارة الذاكرة: حفظ آخر 10 رسائل فقط لعدم إبطاء البوت
    if user_id not in user_memory:
        user_memory[user_id] = []
    
    memory = user_memory[user_id]
    
    system_prompt = (
        "أنت اسمك Sayyaf AI، مساعد ذكي وصديق للمستخدم. مطورك هو المبرمج اليمني سياف طالب. "
        "لا تذكر اسمك أو اسم مطورك إلا إذا سألك المستخدم عن هويتك أو من صنعك. "
        "تحدث بلهجة ودودة، احترافية، ومنظمة جداً. استخدم التنسيق (Bold) والقوائم. "
        "كن صديقاً للمستخدم وتذكر ما قيل في المحادثة."
    )

    # بناء سياق المحادثة
    messages = [{"role": "system", "content": system_instructions if 'system_instructions' in locals() else system_prompt}]
    for msg in memory:
        messages.append(msg)
    messages.append({"role": "user", "content": user_text})

    url = "https://text.pollinations.ai/"
    payload = {
        "messages": messages,
        "model": "openai",
        "private": True # لتجنب رسائل التحذير العامة
    }

    try:
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            ai_reply = response.text
            # حفظ الرد في الذاكرة
            memory.append({"role": "user", "content": user_text})
            memory.append({"role": "assistant", "content": ai_reply})
            if len(memory) > 10: memory.pop(0); memory.pop(0) # تنظيف الذاكرة القديمة
            return ai_reply
    except: return None
    return None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.text: return
    
    # إبقاء "يكتب الآن" مستمراً
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    user_id = update.effective_user.id
    user_text = update.message.text
    
    # تشغيل طلب الذكاء الاصطناعي في Thread منفصل لعدم تجميد البوت
    loop = asyncio.get_event_loop()
    answer = await loop.run_in_executor(None, get_ai_response, user_id, user_text)
    
    if answer:
        await update.message.reply_text(answer, parse_mode='Markdown')
    else:
        await update.message.reply_text("عذراً صديقي، واجهت مشكلة بسيطة. أعد المحاولة؟")

if __name__ == '__main__':
    Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))).start()
    TOKEN = "7965345356:AAEiY2Q3UQ6WZvpFQAAmap0eebvLRvWXVuY"
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    application.run_polling(drop_pending_updates=True)
