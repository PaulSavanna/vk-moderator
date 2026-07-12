from vkbottle.bot import BotLabeler
from bot.handlers.moderation import labeler as mod_labeler
from bot.handlers.admin import labeler as admin_labeler


def setup_handlers(dp: BotLabeler):
    dp.load(mod_labeler)
    dp.load(admin_labeler)
