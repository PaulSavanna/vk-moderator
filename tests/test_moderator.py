import pytest
from bot.services.database import Database
from bot.services.moderator import ModeratorService
from bot.config import get_settings, reset_settings


@pytest.fixture
def db(tmp_path):
    return Database(str(tmp_path / "test.db"))


@pytest.fixture
def mod(db):
    return ModeratorService(db)


@pytest.fixture(autouse=True)
def _reset_config():
    reset_settings()
    yield
    reset_settings()


@pytest.mark.asyncio
async def test_clean_message_passes(db, mod):
    await db.init()
    await db.create_user(123, 456)
    await db.set_captcha_passed(123, 456)

    result = await mod.check_message(123, 456, "Привет всем!")
    assert result is None


@pytest.mark.asyncio
async def test_profanity_triggers_warning(db, mod):
    await db.init()
    await db.create_user(123, 456)
    await db.set_captcha_passed(123, 456)

    result = await mod.check_message(123, 456, "ты хуйни не скажи")
    assert result is not None
    assert result["action"] == "warn"
    assert result["reason"] == "profanity"
    assert result["warnings"] == 1


@pytest.mark.asyncio
async def test_max_warnings_bans(db, mod):
    await db.init()
    await db.create_user(123, 456)
    await db.set_captcha_passed(123, 456)

    settings = get_settings()
    for _ in range(settings.max_warnings - 1):
        await mod.check_message(123, 456, "блять")

    result = await mod.check_message(123, 456, "сука")
    assert result["action"] == "ban"


@pytest.mark.asyncio
async def test_new_user_needs_captcha(db, mod):
    await db.init()

    result = await mod.check_message(123, 456, "Привет")
    assert result is not None
    assert result["action"] == "captcha"


@pytest.mark.asyncio
async def test_banned_user_message_deleted(db, mod):
    await db.init()
    await db.create_user(123, 456)
    await db.set_captcha_passed(123, 456)
    await db.ban_user(123, 456)

    result = await mod.check_message(123, 456, "Привет всем!")
    assert result is not None
    assert result["action"] == "delete"
    assert result["reason"] == "ban"


@pytest.mark.asyncio
async def test_mixed_profanity_and_clean_text(db, mod):
    await db.init()
    await db.create_user(123, 456)
    await db.set_captcha_passed(123, 456)

    result = await mod.check_message(123, 456, "привет хуй всем")
    assert result is not None
    assert result["action"] == "warn"
    assert result["reason"] == "profanity"


@pytest.mark.asyncio
async def test_profanity_checked_before_spam(db, mod):
    await db.init()
    await db.create_user(123, 456)
    await db.set_captcha_passed(123, 456)

    result = await mod.check_message(123, 456, "хуй https://spam.com")
    assert result is not None
    assert result["reason"] == "profanity"


@pytest.mark.asyncio
async def test_spam_url_below_threshold(db, mod):
    await db.init()
    await db.create_user(123, 456)
    await db.set_captcha_passed(123, 456)

    settings = get_settings()
    for _ in range(settings.spam_threshold - 1):
        result = await mod.check_message(123, 456, "https://example.com")
        assert result is None


@pytest.mark.asyncio
async def test_spam_url_at_threshold(db, mod):
    await db.init()
    await db.create_user(123, 456)
    await db.set_captcha_passed(123, 456)

    settings = get_settings()
    for _ in range(settings.spam_threshold):
        result = await mod.check_message(123, 456, "https://example.com")

    assert result["action"] == "warn"
    assert result["reason"] == "spam"


@pytest.mark.asyncio
async def test_repeated_chars_trigger_spam(db, mod):
    await db.init()
    await db.create_user(123, 456)
    await db.set_captcha_passed(123, 456)

    settings = get_settings()
    for _ in range(settings.spam_threshold):
        result = await mod.check_message(123, 456, "aaaaaaaaaa")

    assert result["action"] == "warn"
    assert result["reason"] == "spam"


@pytest.mark.asyncio
async def test_different_users_independent(db, mod):
    await db.init()
    await db.create_user(1, 456)
    await db.set_captcha_passed(1, 456)
    await db.create_user(2, 456)
    await db.set_captcha_passed(2, 456)

    await mod.check_message(1, 456, "хуй")
    await mod.check_message(1, 456, "сука")
    result1 = await mod.check_message(1, 456, "блять")

    result2 = await mod.check_message(2, 456, "Привет!")
    assert result1["action"] == "ban"
    assert result2 is None
