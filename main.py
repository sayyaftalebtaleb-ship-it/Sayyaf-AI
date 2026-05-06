import os, requests, asyncio
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# 1. إعداد Flask لضمان بقاء البوت حياً على Render
app = Flask(__name__)
@app.route('/')
def home(): return "Sayyaf AI is Active", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# 2. مخزن الذاكرة المؤقتة
user_memory = {}

def get_ai_response(user_id, user_text, user_lang):
    if user_id not in user_memory:
        user_memory[user_id] = []
    
    # تحديد الاسم بناءً على اللغة بدقة
    creator = "سياف طالب" if user_lang != 'en' else "Sayyaf Taleb"
    bot_name = "Sayyaf AI"
    
    # التعليمات الصارمة التي طلبتها (بصيغة تضمن السرعة والاستقرار)
    system_prompt = (
        f"أنت {bot_name}. مطورك هو {creator}. "
        "قواعدك المهنية: "
        "1. لا تذكر اسمك أو مطورك نهائياً إلا إذا سألك المستخدم 'من أنت' أو 'من صنعك'. "
        "2. لا تتحدث عن قدراتك أو أسلوب تنظيمك؛ نفذ المهام مباشرة بصمت. "
        "3. عند إنشاء الجداول، يجب أن تكون داخل بلوك كود (```) لتظهر بشكل احترافي. "
        "4. اجعل ردودك منظمة جداً واستخدم التنسيق العريض (Bold). "
        "5. تذكر سياق المحادثة وكن صديقاً ذكياً ومختصراً."
    )

    # بناء الرسائل مع الذاكرة
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(user_memory[user_id][-6:]) # آخر 6 رسائل لسرعة الاستجابة
    messages.append({"role": "user", "content": user_text})

    try:
        # العودة لطلب POST لكن مع رؤوس طلبات (Headers) تجعل السيرفر يعتبرك مستخدماً حقيقياً
        url = "[https://text.pollinations.ai/](https://text.pollinations.ai/)"
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0"
        }
        payload = {
            "messages": messages,
            "model": "openai",
            "private": True
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=45)
        if response.status_code == 200:
            ai_reply = response.text
            # حفظ الذاكرة
            user_memory[user_id].append({"role": "user", "content": user_text})
            user_memory[user_id].append({"role": "assistant", "content": ai_reply})
            return ai_reply
    except: return None
    return None

async def keep_typing(context, chat_id, stop_event):
    """يضمن بقاء وشم الكتابة ظاهراً حتى ظهور الرد"""
    while not stop_event.is_set():
        try:
            await context.bot.send_chat_action(chat_id=chat_id, action="typing")
            await asyncio.sleep(4)
        except: break

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    user_text = update.message.text
    user_lang = update.effective_user.language_code

    # بدء وشم الكتابة
    stop_typing = asyncio.Event()
    typing_task = asyncio.create_task(keep_typing(context, chat_id, stop_typing))
    
    try:
        # جلب الرد في خلفية السيرفر
        loop = asyncio.get_event_loop()
        answer = await loop.run_in_executor(None, get_ai_response, user_id, user_text, user_lang)
        
        # إيقاف الوشم فوراً عند استلام الرد
        stop_typing.set()
        await typing_task
        
        if answer:
            # إرسال الرد بتنسيق Markdown الاحترافي
            try:
                await update.message.reply_text(answer, parse_mode='Markdown')
            except:
                await update.message.reply_text(answer)
        else:
            await update.message.reply_text("عذراً، واجهت مشكلة في الاتصال. يرجى المحاولة مرة أخرى.")
    except:
        stop_typing.set()

if __name__ == '__main__':
    Thread(target=run_flask).start()
    
    # ضع التوكن الخاص بك هنا
    TOKEN = "7965345356:AAEiY2Q3UQ6WZvpFQAAmap0eebvLRvWXVuY"
    
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("Sayyaf AI is launching now...")
    application.run_polling(drop_pending_updates=True)
