from vkbottle.bot import BotLabeler, Message
from vkbottle import Keyboard, KeyboardButtonColor, Text
from bot.services.database import Database
from bot.config import get_settings

labeler = BotLabeler()


def _get_db():
    settings = get_settings()
    return Database(settings.db_path)


def is_admin(user_id: int) -> bool:
    settings = get_settings()
    return user_id in settings.admin_ids


@labeler.message(text="/mod help")
async def cmd_mod_help(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Нет доступа!")
        return

    await message.answer(
        "🛡️ Команды модератора:\n\n"
        "/mod stats — статистика чата\n"
        "/mod ban <id> — забанить\n"
        "/mod unban <id> — разбанить\n"
        "/mod warn <id> — добавить варн\n"
        "/mod reset <id> — сбросить варны\n"
        "/mod check <id> — проверить пользователя"
    )


@labeler.message(text="/mod stats")
async def cmd_stats(message: Message):
    if not is_admin(message.from_user.id):
        return

    db = _get_db()
    stats = await db.get_stats(message.chat_id)
    await message.answer(
        f"📊 Статистика чата:\n\n"
        f"👥 Всего: {stats['total']}\n"
        f"⚠️ С варнами: {stats['warned']}\n"
        f"🚫 Забанены: {stats['banned']}"
    )


@labeler.message(text="/mod ban <user_id>")
async def cmd_ban(message: Message, user_id: str):
    if not is_admin(message.from_user.id):
        return

    db = _get_db()
    try:
        uid = int(user_id)
        await db.ban_user(uid, message.chat_id)
        await message.answer(f"🚫 Пользователь {uid} забанен!")
    except ValueError:
        await message.answer("❌ Укажите ID пользователя")


@labeler.message(text="/mod unban <user_id>")
async def cmd_unban(message: Message, user_id: str):
    if not is_admin(message.from_user.id):
        return

    db = _get_db()
    try:
        uid = int(user_id)
        await db.unban_user(uid, message.chat_id)
        await message.answer(f"✅ Пользователь {uid} разбанен!")
    except ValueError:
        await message.answer("❌ Укажите ID пользователя")


@labeler.message(text="/mod warn <user_id>")
async def cmd_warn(message: Message, user_id: str):
    if not is_admin(message.from_user.id):
        return

    db = _get_db()
    settings = get_settings()
    try:
        uid = int(user_id)
        warnings = await db.add_warning(uid, message.chat_id)
        await message.answer(f"⚠️ Предупреждение добавлено. Всего: {warnings}/{settings.max_warnings}")
    except ValueError:
        await message.answer("❌ Укажите ID пользователя")


@labeler.message(text="/mod reset <user_id>")
async def cmd_reset(message: Message, user_id: str):
    if not is_admin(message.from_user.id):
        return

    db = _get_db()
    try:
        uid = int(user_id)
        await db.reset_warnings(uid, message.chat_id)
        await message.answer(f"✅ Предупреждения сброшены для {uid}")
    except ValueError:
        await message.answer("❌ Укажите ID пользователя")


@labeler.message(text="/mod check <user_id>")
async def cmd_check(message: Message, user_id: str):
    if not is_admin(message.from_user.id):
        return

    db = _get_db()
    settings = get_settings()
    try:
        uid = int(user_id)
        user = await db.get_user(uid, message.chat_id)
        if user:
            status = "🚫 Забанен" if user.is_banned else "✅ Активен"
            await message.answer(
                f"👤 Пользователь {uid}:\n"
                f"Статус: {status}\n"
                f"Предупреждения: {user.warnings}/{settings.max_warnings}\n"
                f"Капча: {'✅ Пройдена' if user.captcha_passed else '❌ Не пройдена'}"
            )
        else:
            await message.answer("❌ Пользователь не найден")
    except ValueError:
        await message.answer("❌ Укажите ID пользователя")
