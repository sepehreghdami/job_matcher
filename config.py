from pydantic_settings import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    telegram_api_id: int
    telegram_api_hash: str
    telegram_phone: str
    telegram_bot_token:str
    database_url: str
    telegram_channels: List[str]

    # Optional proxy for Telegram traffic only (Telethon scraper + bot).
    # The LLM endpoint and Postgres always connect directly. Unset = no proxy.
    # e.g. a v2ray/xray local SOCKS inbound: socks5://127.0.0.1:10808
    telegram_proxy_url: Optional[str] = None

    fetch_interval_minutes:int
    evaluate_interval_minutes:int
    forward_interval_minutes:int
    scoring_batch_size:int
    scoring_max_concurrent:int
    scoring_model:str
    forward_score_threshold:float

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }
    llm_api_key: str
    llm_base_url: str
    # openai_api_key: str

    forward_max_concurrent: int




settings = Settings()