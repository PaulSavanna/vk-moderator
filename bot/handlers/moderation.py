import random
from vkbottle.bot import BotLabeler, Message, MessageEvent
from vkbottle import Keyboard, KeyboardButtonColor, Text
from bot.services.database import Database
from bot.services.moderator import ModeratorService
from bot.config import get_settings

labeler = BotLabeler()


def _get_db_moderator():
    settings = get_settings()
    db = Database(settings.db_path)
    return db, ModeratorService(db)


@labeler.chat_message()
async def handle_chat_message(message: Message):
    if not message.from_id or message.from_id < 0:
        return

    settings = get_settings()
    if message.from_id in settings.admin_ids:
        return

    db, moderator = _get_db_moderator()

    text = message.text or ""
    result = await moderator.check_message(message.from_id, message.chat_id, text)

    if not result:
        return

    if result["action"] == "captcha":
        kb = (
            Keyboard(inline=True)
            .add(Text("✅ Я не робот"), color=KeyboardButtonColor.POSITIVE)
        )
        await message.answer(
            f"👋 Добро пожаловать!\n\n"
            f"Нажми кнопку чтобы подтвердить что ты не робот:",
            keyboard=kb
        )
        return

    if result["action"] == "delete":
        await message.delete()
        return

    if result["action"] == "warn":
        await message.delete()
        await message.answer(
            f"⚠️ @{message.from_id}, осторожно!\n"
            f"Причина: {'мат' if result['reason'] == 'profanity' else 'спам'}\n"
            f"Предупреждения: {result['warnings']}/{settings.max_warnings}"
        )
        return

    if result["action"] == "ban":
        await message.delete()
        await message.answer(
            f"🚫 @{message.from_id} забанен!\n"
            f"Причина: {'превышен лимит предупреждений' if result['reason'] != 'ban' else 'многократные нарушения'}"
        )


@labeler.chat_message(text="✅ Я не робот")
async def handle_captcha(message: Message):
    if not message.from_id or message.from_id < 0:
        return

    db, _ = _get_db_moderator()
    user = await db.get_user(message.from_id, message.chat_id)
    if user and not user.captcha_passed:
        await db.set_captcha_passed(message.from_id, message.chat_id)
        await message.delete()
        await message.answer(
            f"✅ Добро пожаловать в чат!\n"
            f"Соблюдай правила и всё будет хорошо."
        )
