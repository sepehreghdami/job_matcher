
from telegram import Bot
from telegram.error import Forbidden, BadRequest
from schemas.evaluation import EvaluationDto
from schemas.telegram_message import TelegramMessage
from schemas.user import UserDto
from config import settings


_bot = Bot(token=settings.telegram_bot_token)


async def forward_message(evaluation: EvaluationDto, message: TelegramMessage, user: UserDto) -> str:
    if not user.telegram_chat_id:
        return "permanent_failure"

    try:
        await _bot.send_message(
            chat_id=user.telegram_chat_id,
            text=f"🎯 <b>Job Match — Score {evaluation.score:.1f}/10</b>",
            parse_mode="HTML",
        )

        # Reconstruct message text with source attribution
        text = message.text or ""
        # caption = f"\n\n📢 <i>via {message.channel_name}</i>" if message.channel_name else ""

        await _bot.send_message(
            chat_id=user.telegram_chat_id,
            text=text,
            parse_mode="HTML",
            disable_web_page_preview=False,  # lets Telegram auto-preview the job URL in text
        )

        return "ok"

    except (Forbidden, BadRequest) as e:
        print(f"[forward] permanent failure for user_id={user.user_id}: {e}")
        return "permanent_failure"

    except Exception as e:
        print(f"[forward] transient failure for user_id={user.user_id}: {e}")
        return "transient_failure"