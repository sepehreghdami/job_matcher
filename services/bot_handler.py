# services/bot_handler.py

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters, ConversationHandler
from db.engine import get_session
from db.repos.user import batch_save_users
from schemas.user import UserDto
from config import settings

WAITING_FOR_RESUME = 1  # conversation state


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to Jobular!\n\n"
        "Please send me your resume text and I'll start matching job opportunities for you."
    )
    return WAITING_FOR_RESUME


async def receive_resume(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    resume_text = update.message.text.strip()

    if len(resume_text) < 50:
        await update.message.reply_text("That looks too short for a resume. Please send your full resume text.")
        return WAITING_FOR_RESUME  # stay in this state, ask again

    with get_session() as session:
        batch_save_users(
            [UserDto(
                telegram_chat_id=user.id,
                telegram_username=user.username,
                resume_text=resume_text,
                is_active=True,
            )],
            session,
            on_conflict="update",
        )

    await update.message.reply_text(
        "✅ You're all set! I'll notify you when I find job postings that match your profile."
    )
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cancelled. Send /start any time to register.")
    return ConversationHandler.END


def build_bot_app() -> Application:
    app = Application.builder().token(settings.telegram_bot_token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            WAITING_FOR_RESUME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_resume)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    return app