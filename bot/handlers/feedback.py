# bot/handlers/feedback.py
from __future__ import annotations
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, CommandHandler, CallbackQueryHandler, filters
from bot.db.base import Session
from bot.db.crud import get_or_create_user, create_feedback
from bot.settings import OWNER_IDS

WAITING_FEEDBACK: set[int] = set()

async def feedback_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    WAITING_FEEDBACK.add(user.id)
    if update.message:
        await update.message.reply_text("✍️ Please type your feedback now (send one message). Send /cancel to exit.")
    elif update.callback_query:
        await update.callback_query.edit_message_text("✍️ Please type your feedback now (send one message). Send /cancel to exit.")

async def cancel_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id in WAITING_FEEDBACK:
        WAITING_FEEDBACK.remove(user.id)
        await update.message.reply_text("❎ Feedback canceled.")
    else:
        await update.message.reply_text("You're not in feedback mode.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text

    if user.id in WAITING_FEEDBACK:
        WAITING_FEEDBACK.remove(user.id)
        async with Session() as session:
            db_user = await get_or_create_user(
                session,
                tg_id=user.id,
                username=user.username,
                first=user.first_name,
                lang=(user.language_code or None),
            )
            await create_feedback(session, user_id=db_user.id, message=text)

        await update.message.reply_text("🙏 Thanks for your feedback! Saved.")
        # forward to owners
        for oid in OWNER_IDS:
            try:
                await context.bot.send_message(
                    oid,
                    f"💌 Feedback from {user.first_name} (@{user.username} | {user.id}):\n\n{text}"
                )
            except Exception:
                pass
        return True  # consumed as feedback

    return False  # not feedback text

def register_feedback_handlers(app):
    app.add_handler(CommandHandler("feedback", feedback_cmd))
    app.add_handler(CommandHandler("cancel", cancel_feedback))
    app.add_handler(CallbackQueryHandler(feedback_cmd, pattern="^feedback$"))
    # general text handler (must be after /commands)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
