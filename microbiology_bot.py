import logging
import json
import os
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler

# 1. الإعدادات
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = '8697581242:AAGUjdoFAG3NfpNWWZRPztvXdqBl0E2Ju7s'
PASS_CODE = "micro2026"
DATA_FILE = "archive_data.json"
USERS_LOG = "users_log.json" # ملف سجل الزملاء

# حالات المحادثة
STARTING, CHOOSING_SUBJECT, CHOOSING_CATEGORY, CHOOSING_ITEM = range(4)

SUBJECTS = ['Physics', 'Chemistry', 'Botany', 'Zoology', 'IT', 'Culture', 'Microbiology', 'Biochemistry']
CATEGORIES = {'سكشن': 'sec', 'محاضرة': 'lec', 'مراجعة وامتحانات': 'exam'}

# --- وظائف إدارة البيانات ---
def load_data(file_path):
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f: return json.load(f)
        except: return {}
    return {}

def save_data(file_path, data):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def log_user(user):
    logs = load_data(USERS_LOG)
    user_id = str(user.id)
    logs[user_id] = {
        "username": user.username,
        "full_name": user.full_name,
        "last_seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    save_data(USERS_LOG, logs)

# --- وظيفة الجروب (التسجيل) ---
async def archive_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in ['group', 'supergroup']:
        text = update.message.text or update.message.caption
        if text and text.startswith("تسجيل"):
            key = text.replace("تسجيل", "").strip().lower()
            archive = load_data(DATA_FILE)
            archive[key] = {"chat_id": update.effective_chat.id, "message_id": update.message.message_id}
            save_data(DATA_FILE, archive)
            await update.message.reply_text(f"✅ تم الربط بالكود: {key}")

# --- نظام الخاص (الأزرار والرجوع) ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("🔐 أهلاً بك! أرسل كلمة مرور القسم:")
    return STARTING

async def verify_pass(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text == PASS_CODE:
        log_user(update.effective_user) # تسجيل بيانات الزميل
        return await show_main_menu(update, context)
    await update.message.reply_text("❌ كلمة السر خطأ!")
    return STARTING

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [SUBJECTS[i:i+2] for i in range(0, len(SUBJECTS), 2)]
    text = "✅ تم التحقق! اختر المادة:"
    if update.callback_query:
        await update.callback_query.message.edit_text(text, reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    else:
        await update.message.reply_text(text, reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    return CHOOSING_SUBJECT

async def select_subject(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    subject = update.message.text
    if subject not in SUBJECTS: return CHOOSING_SUBJECT
    
    context.user_data['subject'] = subject
    keyboard = [[cat] for cat in CATEGORIES.keys()]
    keyboard.append(['⬅️ رجوع للقائمة الرئيسية']) # زر الرجوع
    
    await update.message.reply_text(f"📂 اختر القسم في {subject}:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    return CHOOSING_CATEGORY

async def select_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    category_name = update.message.text
    
    if category_name == '⬅️ رجوع للقائمة الرئيسية':
        return await show_main_menu(update, context)
        
    if category_name not in CATEGORIES: return CHOOSING_CATEGORY
    
    subject = context.user_data['subject']
    category_code = CATEGORIES[category_name]
    
    buttons = []
    for i in range(1, 8):
        callback_data = f"{subject.lower()}_{category_code}_{i}"
        buttons.append([InlineKeyboardButton(f"{category_name} رقم {i}", callback_data=callback_data)])
    
    # إضافة زر رجوع للخلف (داخل الـ Inline)
    buttons.append([InlineKeyboardButton("🔙 رجوع لاختيار القسم", callback_data="back_to_categories")])
    
    await update.message.reply_text(f"📍 محتوى {subject} - {category_name}:", reply_markup=InlineKeyboardMarkup(buttons))
    return CHOOSING_ITEM

async def handle_inline_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "back_to_categories":
        subject = context.user_data.get('subject')
        keyboard = [[cat] for cat in CATEGORIES.keys()]
        keyboard.append(['⬅️ رجوع للقائمة الرئيسية'])
        await query.message.delete() # مسح رسالة الـ Inline لعدم اللخبطة
        await context.bot.send_message(chat_id=query.message.chat_id, text=f"📂 اختر القسم في {subject}:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
        return CHOOSING_CATEGORY
    
    # عملية إرسال الملف
    file_key = query.data
    archive = load_data(DATA_FILE)
    if file_key in archive:
        await context.bot.forward_message(chat_id=query.message.chat_id, from_chat_id=archive[file_key]["chat_id"], message_id=archive[file_key]["message_id"])
    else:
        await query.message.reply_text(f"❌ لم يتم رفع ملف لهذا الزرار.\nالكود: {file_key}")
    return CHOOSING_ITEM

# أمر خاص بك أنت فقط لرؤية الزملاء الذين سجلوا
async def show_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # يمكنك إضافة حماية هنا ليعمل معك أنت فقط عن طريق الـ ID الخاص بك
    logs = load_data(USERS_LOG)
    if not logs:
        await update.message.reply_text("لا يوجد زوار بعد.")
        return
    
    report = "👥 سجل الزملاء الذين دخلوا البوت:\n\n"
    for uid, info in logs.items():
        report += f"👤 {info['full_name']} (@{info['username']})\n🗓 {info['last_seen']}\n\n"
    await update.message.reply_text(report)

def main():
    application = Application.builder().token(TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            STARTING: [MessageHandler(filters.TEXT & ~filters.COMMAND, verify_pass)],
            CHOOSING_SUBJECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_subject)],
            CHOOSING_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_category)],
            CHOOSING_ITEM: [CallbackQueryHandler(handle_inline_buttons)],
        },
        fallbacks=[CommandHandler("start", start)],
    )
    application.add_handler(CommandHandler("show_logs", show_logs)) # أمر لرؤية السجل
    application.add_handler(conv_handler)
    application.add_handler(MessageHandler(filters.ChatType.GROUPS, archive_handler))
    application.run_polling()

if __name__ == '__main__':
    main()
