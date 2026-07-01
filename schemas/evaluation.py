
from pydantic import BaseModel,Field
from typing import Optional
from datetime import datetime


class EvaluationDto(BaseModel):
    id: Optional[int] = None
    message_pk: int
    user_id: int
    score: Optional[float] = Field(None, ge=0, le=10)
    reason: Optional[str] = None
    processed_at: Optional[datetime] = None
    forwarded_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}