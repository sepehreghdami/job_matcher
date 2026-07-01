# services/bot_handler.py

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters, ConversationHandler
from db.engine import get_session
from db.repos.user import batch_save_users
from schemas.user import UserDto
from config import settings
from services.proxy import get_proxy_url
from services.pdf_service import extract_pdf_text

WAITING_FOR_RESUME = 1  # conversation state
MIN_RESUME_LEN = 50     # shorter than this isn't a usable resume


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to Jobular!\n\n"
        "Send me your resume — either paste the text or upload it as a PDF — "
        "and I'll start matching job opportunities for you."
    )
    return WAITING_FOR_RESUME


async def _save_resume(update: Update, resume_text: str):
    """Persist the resume and confirm to the user. Ends the conversation."""
    user = update.effective_user
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


async def receive_resume(update: Update, context: ContextTypes.DEFAULT_TYPE):
    resume_text = update.message.text.strip()

    if len(resume_text) < MIN_RESUME_LEN:
        await update.message.reply_text("That looks too short for a resume. Please send your full resume text.")
        return WAITING_FOR_RESUME  # stay in this state, ask again

    return await _save_resume(update, resume_text)


async def receive_resume_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document

    tg_file = await document.get_file()
    data = bytes(await tg_file.download_as_bytearray())
    resume_text = extract_pdf_text(data)

    if len(resume_text) < MIN_RESUME_LEN:
        await update.message.reply_text(
            "❌ I couldn't read any text from that PDF (it may be scanned or image-only). "
            "Please try another PDF or paste your resume text instead."
        )
        return WAITING_FOR_RESUME  # stay in this state, ask again

    return await _save_resume(update, resume_text)


async def receive_unsupported(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Please paste your resume as text or upload it as a PDF."
    )
    return WAITING_FOR_RESUME  # stay in this state, ask again


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cancelled. Send /start any time to register.")
    return ConversationHandler.END


def build_bot_app() -> Application:
    builder = Application.builder().token(settings.telegram_bot_token)

    proxy = get_proxy_url()
    if proxy:
        # proxy() covers bot API calls; get_updates_proxy() covers long-polling.
        builder = builder.proxy(proxy).get_updates_proxy(proxy)

    app = builder.build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            WAITING_FOR_RESUME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_resume),
                MessageHandler(filters.Document.PDF, receive_resume_pdf),
                # Anything else (images, other docs, stickers…) — nudge back on track.
                MessageHandler(~filters.COMMAND, receive_unsupported),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    return app