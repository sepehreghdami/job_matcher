from pydantic import BaseModel,ConfigDict
from typing import Optional
from datetime import datetime



# schemas/user.py
class UserDto(BaseModel):
    user_id: Optional[int] = None        # ← add = None
    telegram_chat_id: Optional[int] = None
    telegram_username: Optional[str] = None
    resume_text: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None  # ← add = None

    model_config = ConfigDict(from_attributes=True)