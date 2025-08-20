# bot/main.py
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from .settings import BOT_TOKEN, OWNER_IDS

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("bot")

MENU = InlineKeyboardMarkup([
    [InlineKeyboardButton("📝 Feedback (Day 3)", callback_data="feedback"),
     InlineKeyboardButton("ℹ️ About", callback_data="about")],
    [InlineKeyboardButton("❓ Help", callback_data="help")],
])

def _users_set(app) -> set:
    if "users" not in app.bot_data:
        app.bot_data["users"] = set()
    return app.bot_data["users"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    _users_set(context.application).add(user.id)
    await update.message.reply_text(f"Hi {user.first_name}! 👋\nChoose an option:", reply_markup=MENU)

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Commands:\n/start\n/help\n/stats (owner only)")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in OWNER_IDS:
        return await update.message.reply_text("⛔ Not allowed.")
    users = _users_set(context.application)
    await update.message.reply_text(f"📊 Unique users (this run): {len(users)}")

async def on_about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    await q.edit_message_text("Sample bot (python-telegram-bot v21, async).")

async def on_help_btn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    await q.edit_message_text("Use the menu or /help.")

async def on_feedback_soon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    await q.edit_message_text("Feedback form arrives on Day 3 ✅")

async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE):
    log.exception("Unhandled error: %s", context.error)

def main():  # <-- sync
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is missing in your .env")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("stats", stats))

    app.add_handler(CallbackQueryHandler(on_about, pattern="^about$"))
    app.add_handler(CallbackQueryHandler(on_help_btn, pattern="^help$"))
    app.add_handler(CallbackQueryHandler(on_feedback_soon, pattern="^feedback$"))

    app.add_error_handler(on_error)

    # No await here; PTB manages the loop
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
