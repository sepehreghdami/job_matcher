
from telegram import Bot
from telegram.error import Forbidden, BadRequest
from telegram.request import HTTPXRequest
from schemas.evaluation import EvaluationDto
from schemas.telegram_message import TelegramMessage
from schemas.user import UserDto
from config import settings
from services.proxy import get_proxy_url

_bot = None


def _get_bot() -> Bot:
    global _bot
    if _bot is None:
        proxy = get_proxy_url()
        if proxy:
            _bot = Bot(
                token=settings.telegram_bot_token,
                request=HTTPXRequest(proxy=proxy),
            )
        else:
            _bot = Bot(token=settings.telegram_bot_token)
    return _bot


async def forward_message(
    evaluation: EvaluationDto,
    message: TelegramMessage,
    user: UserDto,
) -> str:
    if not user.telegram_chat_id:
        return "permanent_failure"

    bot = _get_bot()

    try:
        webpage = getattr(message.media, "webpage", None)

        site_name = getattr(webpage, "site_name", None)
        url = getattr(webpage, "url", None)
        channel_username = getattr(message.channel_username, "username", None)

        parts = [
            f"🎯 <b>Job Match — Score {evaluation.score:.1f}/10</b>"
        ]

        if site_name:
            parts.append(f"📢 <i>via {site_name}</i>")

        if message.text:
            parts.append(message.text)

        if url:
            parts.append(url)

        if channel_username:
            parts.append(channel_username)

        final_message = "\n\n".join(parts)

        await bot.send_message(
            chat_id=user.telegram_chat_id,
            text=final_message,
            parse_mode="HTML",
            disable_web_page_preview=False,
        )

        return "ok"

    except (Forbidden, BadRequest) as e:
        print(f"[forward] permanent failure for user_id={user.user_id}: {e} and for message: {message.id}")
        return "permanent_failure"

    except Exception as e:
        print(
            f"[forward] transient failure "
            f"type={type(e).__name__} "
            f"user_id={user.user_id}: {e}"
            f" and for message: {message.id}"
        )
        return "transient_failure"