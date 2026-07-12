import asyncio
import re
from bot.services.database import Database
from bot.config import get_settings


class ModeratorService:
    def __init__(self, db: Database):
        self.db = db
        self._locks: dict[tuple[int, int], asyncio.Lock] = {}
        self.spam_patterns = [
            r"(.)\1{5,}",
            r"https?://\S+",
            r"(vk\.com|t\.me|bit\.ly)\S*",
        ]
        self.ban_words = [
            "хуй", "пизд", "бля", "еба", "ёба", "сука", "сук",
            "нахуй", "нахер", "блять", "ебать", "пидор",
        ]

    def _get_lock(self, user_id: int, chat_id: int) -> asyncio.Lock:
        key = (user_id, chat_id)
        if key not in self._locks:
            self._locks[key] = asyncio.Lock()
        return self._locks[key]

    async def check_message(self, user_id: int, chat_id: int, text: str) -> dict | None:
        lock = self._get_lock(user_id, chat_id)
        async with lock:
            settings = get_settings()
            user = await self.db.get_user(user_id, chat_id)
            if not user:
                user = await self.db.create_user(user_id, chat_id)

            if user.is_banned:
                return {"action": "delete", "reason": "ban"}

            if not user.captcha_passed:
                return {"action": "captcha", "reason": "new_user"}

            if self._check_profanity(text):
                await self.db.add_warning(user_id, chat_id)
                user = await self.db.get_user(user_id, chat_id)
                if user.warnings >= settings.max_warnings:
                    await self.db.ban_user(user_id, chat_id)
                    return {"action": "ban", "reason": "profanity", "warnings": user.warnings}
                return {"action": "warn", "reason": "profanity", "warnings": user.warnings}

            if await self._check_spam(user_id, chat_id, text):
                await self.db.add_warning(user_id, chat_id)
                user = await self.db.get_user(user_id, chat_id)
                if user.warnings >= settings.max_warnings:
                    await self.db.ban_user(user_id, chat_id)
                    return {"action": "ban", "reason": "spam", "warnings": user.warnings}
                return {"action": "warn", "reason": "spam", "warnings": user.warnings}

            return None

    def _check_profanity(self, text: str) -> bool:
        text_lower = text.lower()
        return any(word in text_lower for word in self.ban_words)

    async def _check_spam(self, user_id: int, chat_id: int, text: str) -> bool:
        settings = get_settings()
        for pattern in self.spam_patterns:
            if re.search(pattern, text):
                await self.db.log_spam(user_id, chat_id, text)
                count = await self.db.get_spam_count(user_id, chat_id, settings.spam_interval)
                return count >= settings.spam_threshold
        return False
