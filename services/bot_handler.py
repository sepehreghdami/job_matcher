# services/bot_handler.py

import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters, ConversationHandler
from db.engine import get_session
from db.repos.user import batch_save_users, set_user_active
from schemas.user import UserDto
from config import settings
from services.proxy import get_proxy_url
from services.pdf_service import extract_pdf_text
from services.docx_service import extract_docx_text

logger = logging.getLogger(__name__)

WAITING_FOR_RESUME = 1  # conversation state
MIN_RESUME_LEN = 50     # shorter than this isn't a usable resume

DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("[bot] /start from user_id=%s username=%s", update.effective_user.id, update.effective_user.username)
    await update.message.reply_text(
        "👋 Welcome to Jobular!\n\n"
        "Send me your resume — paste the text, or upload it as a PDF or Word (.docx) file — "
        "and I'll start matching job opportunities for you.\n\n"
        "Later on you can use:\n"
        "/updatecv — replace your resume\n"
        "/unsubscribe — stop receiving matches\n"
        "/subscribe — turn matches back on"
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

    logger.info("[bot] resume saved for user_id=%s (%d chars)", user.id, len(resume_text))
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


async def receive_resume_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document
    is_pdf = document.mime_type == "application/pdf"
    kind = "PDF" if is_pdf else "Word file"

    logger.info("[bot] user_id=%s uploaded a %s (%d bytes)", update.effective_user.id, kind, document.file_size or 0)

    tg_file = await document.get_file()
    data = bytes(await tg_file.download_as_bytearray())
    resume_text = extract_pdf_text(data) if is_pdf else extract_docx_text(data)

    if len(resume_text) < MIN_RESUME_LEN:
        logger.warning("[bot] user_id=%s: could not extract usable text from %s", update.effective_user.id, kind)
        await update.message.reply_text(
            f"❌ I couldn't read any text from that {kind} (it may be scanned, image-only, or corrupted). "
            "Please try another file or paste your resume text instead."
        )
        return WAITING_FOR_RESUME  # stay in this state, ask again

    return await _save_resume(update, resume_text)


async def receive_unsupported(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Please paste your resume as text, or upload it as a PDF or Word (.docx) file."
    )
    return WAITING_FOR_RESUME  # stay in this state, ask again


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cancelled. Send /start any time to register.")
    return ConversationHandler.END


async def updatecv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("[bot] /updatecv from user_id=%s", update.effective_user.id)
    await update.message.reply_text(
        "Send me your new resume — paste the text, or upload it as a PDF or Word (.docx) file — "
        "and I'll replace your current one."
    )
    return WAITING_FOR_RESUME


async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    with get_session() as session:
        updated = set_user_active(user.id, is_active=False, session=session)

    if updated:
        logger.info("[bot] user_id=%s unsubscribed", user.id)
        await update.message.reply_text(
            "🛑 You've been unsubscribed. I won't send you any more job matches. "
            "Send /subscribe any time to turn matches back on."
        )
    else:
        logger.info("[bot] user_id=%s tried /unsubscribe but is not registered", user.id)
        await update.message.reply_text(
            "You're not registered yet, so there's nothing to unsubscribe from. "
            "Send /start to sign up."
        )
    return ConversationHandler.END


async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Re-activate an existing (currently inactive) user. New users should use /start."""
    user = update.effective_user
    with get_session() as session:
        updated = set_user_active(user.id, is_active=True, session=session)

    if updated:
        logger.info("[bot] user_id=%s subscribed", user.id)
        await update.message.reply_text(
            "✅ You're subscribed again! I'll notify you when I find job postings that match your profile."
        )
    else:
        logger.info("[bot] user_id=%s tried /subscribe but is not registered", user.id)
        await update.message.reply_text(
            "You're not registered yet. Send /start to sign up with your resume."
        )
    return ConversationHandler.END


def build_bot_app() -> Application:
    builder = Application.builder().token(settings.telegram_bot_token)

    proxy = get_proxy_url()
    logger.info("Building bot application (proxy=%s)", "enabled" if proxy else "direct")
    if proxy:
        # proxy() covers bot API calls; get_updates_proxy() covers long-polling.
        builder = builder.proxy(proxy).get_updates_proxy(proxy)

    app = builder.build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CommandHandler("updatecv", updatecv),
            CommandHandler("unsubscribe", unsubscribe),
            CommandHandler("subscribe", subscribe),
        ],
        states={
            WAITING_FOR_RESUME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_resume),
                MessageHandler(
                    filters.Document.PDF | filters.Document.MimeType(DOCX_MIME),
                    receive_resume_file,
                ),
                # Anything else (images, other docs, stickers…) — nudge back on track.
                MessageHandler(~filters.COMMAND, receive_unsupported),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CommandHandler("updatecv", updatecv),
            CommandHandler("unsubscribe", unsubscribe),
            CommandHandler("subscribe", subscribe),
        ],
    )

    app.add_handler(conv_handler)
    return app