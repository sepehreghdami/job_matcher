from telethon.tl.types import (
    MessageMediaWebPage,
    MessageMediaPhoto,
    MessageMediaDocument,
)
from schemas.telegram_message import (
    TelegramMessage,
    MessageEntity,
    MediaInfo,
    WebPageMedia,
    Engagement,
    ForwardInfo,
)


def telethon_msg_to_model(msg) -> TelegramMessage:
    """
    Convert a Telethon Message object
    into a clean Pydantic TelegramMessage model.
    """

    # -------------------------
    # Entities
    # -------------------------
    entities = []

    if msg.entities:
        for ent in msg.entities:
            entities.append(
                MessageEntity(
                    type=type(ent).__name__,
                    offset=getattr(ent, "offset", 0),
                    length=getattr(ent, "length", 0),
                    url=getattr(ent, "url", None),
                )
            )

    # -------------------------
    # Media
    # -------------------------
    media_info = None

    if msg.media:

        # Webpage preview
        if isinstance(msg.media, MessageMediaWebPage):
            wp = msg.media.webpage

            media_info = MediaInfo(
                type="webpage",
                webpage=WebPageMedia(
                    url=getattr(wp, "url", None),
                    title=getattr(wp, "title", None),
                    description=getattr(wp, "description", None),
                    site_name=getattr(wp, "site_name", None),
                    photo_id=getattr(getattr(wp, "photo", None), "id", None),
                ),
            )

        # Photo
        elif isinstance(msg.media, MessageMediaPhoto):
            media_info = MediaInfo(type="photo")

        # Document
        elif isinstance(msg.media, MessageMediaDocument):
            media_info = MediaInfo(type="document")

        else:
            media_info = MediaInfo(type=type(msg.media).__name__)

    # -------------------------
    # Engagement
    # -------------------------
    engagement = Engagement(
        views=getattr(msg, "views", None),
        forwards=getattr(msg, "forwards", None),
        replies=getattr(getattr(msg, "replies", None), "replies", None),
        reactions=(
            msg.reactions.to_dict() if getattr(msg, "reactions", None) else None
        ),
    )

    # -------------------------
    # Forward info
    # -------------------------
    forward = None

    if msg.fwd_from:
        fwd = msg.fwd_from

        forward = ForwardInfo(
            from_id=getattr(getattr(fwd, "from_id", None), "user_id", None),
            channel_id=getattr(getattr(fwd, "from_id", None), "channel_id", None),
            date=getattr(fwd, "date", None),
        )

    # -------------------------
    # Channel ID extraction
    # -------------------------
    channel_id = None

    if msg.peer_id:
        channel_id = getattr(msg.peer_id, "channel_id", None)

    # -------------------------
    # Final model
    # -------------------------
    return TelegramMessage(
        id=msg.id,
        channel_id=channel_id,
        date=msg.date,
        edit_date=msg.edit_date,
        text=msg.message,
        entities=entities,
        media=media_info,
        engagement=engagement,
        post_author=getattr(msg, "post_author", None),
        grouped_id=getattr(msg, "grouped_id", None),
        forward=forward,
    )
