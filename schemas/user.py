from pydantic import BaseModel,Field
from typing import Optional
from datetime import datetime

class UserDto(BaseModel):
    user_id: int
    telegram_username: Optional[str] = None
    resume_text: Optional[str] = None
    created_at: datetime
    is_active: bool = True
    
    model_config = {"from_attributes": True}

