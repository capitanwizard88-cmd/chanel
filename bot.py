python-telegram-bot==20.6
web: python bot.py
# bot.py
import os
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# --- تنظیمات از environment ---
BOT_TOKEN = os.environ.get("8398453470:AAG_Q0ufyaVh5dm6BZcXI5AmL1m4EDo4jTY")
CHANNEL_USERNAME = os.environ.get("@darsi7788")  # مثال: @mychannel

if not BOT_TOKEN or not CHANNEL_USERNAME:
    raise RuntimeError("8398453470:AAG_Q0ufyaVh5dm6BZcXI5AmL1m4EDo4jTY و @darsi7788 باید در محیط (ENV) تنظیم شده باشند")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# نگهداری فایل‌ها (ساده: در حافظه) — بعدا می‌تونی sqlite بذاری
FILES = {}

# بررسی عضویت کاربر در کانال
async def is_member_of_channel(app, user_id: int) -> bool:
    try:
        member = await app.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in ("member", "creator", "administrator")
    except Exception as e:
        logger.warning("get_chat_member failed: %s", e)
        return False

# handler برای /start (پارامتر از deep link میاد: /start FILEKEY)
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args or []
    if not args:
        await update.message.reply_text("سلام! از دکمه دانلود داخل کانال استفاده کن.")
        return

    file_key = args[0]
    if file_key not in FILES:
        await update.message.reply_text("فایل پیدا نشد یا هنوز آماده نشده.")
        return

    app = context.application
    if await is_member_of_channel(app, user.id):
        info = FILES[file_key]
        # ترجیح: از file_id استفاده کنیم (آپلود یک‌بار در تلگرام)
        if info.get("file_id"):
            await app.bot.send_document(chat_id=user.id, document=info["file_id"], filename=info.get("filename"))
        else:
            await update.message.reply_text("فایل آماده‌ی ارسال نیست. با ادمین تماس بگیر.")
    else:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(text="رفتن به کانال و عضو شدن", url=f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}")],
            [InlineKeyboardButton(text="من عضو شدم — بررسی کن", callback_data=f"checkjoin|{file_key}")]
        ])
        await update.message.reply_text(f"برای دانلود این فایل ابتدا باید عضو کانال {CHANNEL_USERNAME} بشی.", reply_markup=keyboard)

# callback وقتی کاربر زد «من عضو شدم — بررسی کن»
async def checkjoin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    _, file_key = query.data.split("|", 1)
    app = context.application
    if await is_member_of_channel(app, user.id):
        info = FILES.get(file_key)
        if not info:
            await query.edit_message_text("فایل پیدا نشد.")
            return
        if info.get("file_id"):
            await app.bot.send_document(chat_id=user.id, document=info["file_id"], filename=info.get("filename"))
            await query.edit_message_text("✅ فایل برایت ارسال شد (چت خصوصی).")
        else:
            await query.edit_message_text("فایل هنوز آماده نیست، با ادمین تماس بگیر.")
    else:
        await query.edit_message_text("هنوز عضویت شما دیده نشد؛ مطمئن شو عضو شدی و دوباره دکمه بررسی رو بزن.")

# دستور ادمینی برای ذخیره فایل (ریپلای فایل به این دستور)
async def addfile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message or not update.message.reply_to_message.document:
        await update.message.reply_text("این دستور باید ریپلای یک فایل (document) باشه.\nاستفاده: ریپلای فایل + /addfile FILEKEY")
        return
    args = context.args or []
    if not args:
        await update.message.reply_text("استفاده: /addfile FILEKEY (مثال: /addfile file1)")
        return
    file_key = args[0]
    doc = update.message.reply_to_message.document
    FILES[file_key] = {"file_id": doc.file_id, "filename": doc.file_name}
    bot_user = (await context.application.bot.get_me()).username
    await update.message.reply_text(f"فایل ذخیره شد با کلید `{file_key}`.\nلینک دانلود برای گذاشتن در کانال:\nhttps://t.me/{bot_user}?start={file_key}")

# راه‌اندازی اپ
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    bot_user = (await app.bot.get_me()).username
    print(f"Bot running as @{bot_user}")
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CallbackQueryHandler(checkjoin_callback, pattern=r"^checkjoin\|"))
    app.add_handler(CommandHandler("addfile", addfile_command))
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
