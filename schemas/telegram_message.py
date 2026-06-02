
from pydantic import BaseModel
from typing import Optional,List
from datetime import datetime

class MessageEntity(BaseModel):
    type: str
    offset: int
    length: int
    url: Optional[str] = None


class WebPageMedia(BaseModel):
    url: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    site_name: Optional[str] = None
    photo_id: Optional[int] = None


class MediaInfo(BaseModel):
    type: Optional[str] = None   # photo | document | webpage | video | etc
    webpage: Optional[WebPageMedia] = None


class Engagement(BaseModel):
    views: Optional[int] = None
    forwards: Optional[int] = None
    replies: Optional[int] = None
    reactions: Optional[dict] = None


class ForwardInfo(BaseModel):
    from_id: Optional[int] = None
    channel_id: Optional[int] = None
    date: Optional[datetime] = None

class TelegramMessage(BaseModel):
    pk: Optional[int] = None   
    id: int                    
    channel_id: int
    date: datetime
    edit_date: Optional[datetime] = None
    text: Optional[str] = None
    entities: List[MessageEntity] = []
    media: Optional[MediaInfo] = None
    engagement: Optional[Engagement] = None
    post_author: Optional[str] = None
    grouped_id: Optional[int] = None
    forward: Optional[ForwardInfo] = None