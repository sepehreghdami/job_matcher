
from telegram import Bot
from telegram.error import Forbidden, BadRequest
from schemas.evaluation import EvaluationDto
from schemas.telegram_message import TelegramMessage
from schemas.user import UserDto
from config import settings


_bot = Bot(token=settings.telegram_bot_token)


async def forward_message(evaluation: EvaluationDto, message: TelegramMessage, user: UserDto) -> str:
    """
    Forwards the original Telegram message to the user.
    Returns 'ok', 'permanent_failure', or 'transient_failure'.
    """
    if not user.telegram_chat_id:
        print(f"[forward] user_id={user.user_id} has no telegram_chat_id, skipping")
        return "permanent_failure"

    # print(user.telegram_chat_id)
    try:
        # send score notification first
        await _bot.send_message(
            chat_id=user.telegram_chat_id,
            text=f"🎯 <b>Job Match — Score {evaluation.score:.1f}/10</b>",
            parse_mode="HTML",
        )

        # forward the original message as-is — preserves media, formatting, links
        await _bot.forward_message(
            chat_id=user.telegram_chat_id,
            from_chat_id=message.channel_id,
            message_id=message.id,           # telegram message_id, not DB pk
        )

        return "ok"

    except (Forbidden, BadRequest) as e:
        print(f"[forward] permanent failure for user_id={user.user_id}: {e}")
        return "permanent_failure"

    except Exception as e:
        print(f"[forward] transient failure for user_id={user.user_id}: {e}")
        return "transient_failure"