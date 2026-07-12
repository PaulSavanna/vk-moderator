from dataclasses import dataclass
from dotenv import load_dotenv
import os

_load_dotenv_done = False


def _ensure_env():
    global _load_dotenv_done
    if not _load_dotenv_done:
        load_dotenv()
        _load_dotenv_done = True


@dataclass(frozen=True)
class Settings:
    vk_token: str
    admin_ids: list[int]
    db_path: str = "moderator.db"
    max_warnings: int = 3
    spam_threshold: int = 5
    spam_interval: int = 10


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _ensure_env()
        admin_str = os.environ.get("ADMIN_IDS", "")
        admin_ids = [int(x.strip()) for x in admin_str.split(",") if x.strip()]
        _settings = Settings(
            vk_token=os.environ.get("VK_TOKEN", "test-token"),
            admin_ids=admin_ids,
        )
    return _settings


def reset_settings():
    global _settings
    _settings = None
