import aiosqlite
from bot.models.user import User


class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path

    async def init(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER NOT NULL,
                    chat_id INTEGER NOT NULL,
                    warnings INTEGER DEFAULT 0,
                    is_banned INTEGER DEFAULT 0,
                    captcha_passed INTEGER DEFAULT 0,
                    PRIMARY KEY (user_id, chat_id)
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS spam_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    chat_id INTEGER NOT NULL,
                    message TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await db.commit()

    async def get_user(self, user_id: int, chat_id: int) -> User | None:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM users WHERE user_id = ? AND chat_id = ?",
                (user_id, chat_id),
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return User(
                        user_id=row["user_id"],
                        chat_id=row["chat_id"],
                        warnings=row["warnings"],
                        is_banned=bool(row["is_banned"]),
                        captcha_passed=bool(row["captcha_passed"]),
                    )
                return None

    async def create_user(self, user_id: int, chat_id: int) -> User:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR IGNORE INTO users (user_id, chat_id) VALUES (?, ?)",
                (user_id, chat_id),
            )
            await db.commit()
        return await self.get_user(user_id, chat_id) or User(user_id=user_id, chat_id=chat_id)

    async def add_warning(self, user_id: int, chat_id: int) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE users SET warnings = warnings + 1 WHERE user_id = ? AND chat_id = ?",
                (user_id, chat_id),
            )
            await db.commit()
            user = await self.get_user(user_id, chat_id)
            return user.warnings if user else 0

    async def ban_user(self, user_id: int, chat_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE users SET is_banned = 1 WHERE user_id = ? AND chat_id = ?",
                (user_id, chat_id),
            )
            await db.commit()

    async def unban_user(self, user_id: int, chat_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE users SET is_banned = 0, warnings = 0 WHERE user_id = ? AND chat_id = ?",
                (user_id, chat_id),
            )
            await db.commit()

    async def reset_warnings(self, user_id: int, chat_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE users SET warnings = 0 WHERE user_id = ? AND chat_id = ?",
                (user_id, chat_id),
            )
            await db.commit()

    async def set_captcha_passed(self, user_id: int, chat_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE users SET captcha_passed = 1 WHERE user_id = ? AND chat_id = ?",
                (user_id, chat_id),
            )
            await db.commit()

    async def log_spam(self, user_id: int, chat_id: int, message: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO spam_log (user_id, chat_id, message) VALUES (?, ?, ?)",
                (user_id, chat_id, message),
            )
            await db.commit()

    async def get_spam_count(self, user_id: int, chat_id: int, interval_seconds: int = 10) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                """SELECT COUNT(*) as cnt FROM spam_log 
                   WHERE user_id = ? AND chat_id = ? 
                   AND created_at > datetime('now', ? || ' seconds')""",
                (user_id, chat_id, -interval_seconds),
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

    async def get_stats(self, chat_id: int) -> dict:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT COUNT(*) as total FROM users WHERE chat_id = ?",
                (chat_id,),
            ) as cursor:
                total = (await cursor.fetchone())[0]

            async with db.execute(
                "SELECT COUNT(*) as banned FROM users WHERE chat_id = ? AND is_banned = 1",
                (chat_id,),
            ) as cursor:
                banned = (await cursor.fetchone())[0]

            async with db.execute(
                "SELECT COUNT(*) as warned FROM users WHERE chat_id = ? AND warnings > 0",
                (chat_id,),
            ) as cursor:
                warned = (await cursor.fetchone())[0]

            return {"total": total, "banned": banned, "warned": warned}
