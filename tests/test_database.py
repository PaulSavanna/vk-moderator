import pytest
from bot.services.database import Database


@pytest.fixture
def db(tmp_path):
    return Database(str(tmp_path / "test.db"))


@pytest.mark.asyncio
async def test_init_db(db):
    await db.init()
    user = await db.get_user(123, 456)
    assert user is None


@pytest.mark.asyncio
async def test_create_and_get_user(db):
    await db.init()
    user = await db.create_user(123, 456)
    assert user.user_id == 123
    assert user.chat_id == 456
    assert user.warnings == 0
    assert user.is_banned is False


@pytest.mark.asyncio
async def test_add_warning(db):
    await db.init()
    await db.create_user(123, 456)
    warnings = await db.add_warning(123, 456)
    assert warnings == 1
    warnings = await db.add_warning(123, 456)
    assert warnings == 2


@pytest.mark.asyncio
async def test_ban_user(db):
    await db.init()
    await db.create_user(123, 456)
    await db.ban_user(123, 456)
    user = await db.get_user(123, 456)
    assert user.is_banned is True


@pytest.mark.asyncio
async def test_unban_user(db):
    await db.init()
    await db.create_user(123, 456)
    await db.ban_user(123, 456)
    await db.unban_user(123, 456)
    user = await db.get_user(123, 456)
    assert user.is_banned is False
    assert user.warnings == 0


@pytest.mark.asyncio
async def test_reset_warnings(db):
    await db.init()
    await db.create_user(123, 456)
    await db.add_warning(123, 456)
    await db.add_warning(123, 456)
    await db.reset_warnings(123, 456)
    user = await db.get_user(123, 456)
    assert user.warnings == 0


@pytest.mark.asyncio
async def test_set_captcha_passed(db):
    await db.init()
    await db.create_user(123, 456)
    user = await db.get_user(123, 456)
    assert user.captcha_passed is False
    await db.set_captcha_passed(123, 456)
    user = await db.get_user(123, 456)
    assert user.captcha_passed is True


@pytest.mark.asyncio
async def test_log_and_get_spam_count(db):
    await db.init()
    await db.log_spam(123, 456, "spam1")
    await db.log_spam(123, 456, "spam2")
    count = await db.get_spam_count(123, 456, interval_seconds=60)
    assert count == 2


@pytest.mark.asyncio
async def test_spam_count_isolates_by_user(db):
    await db.init()
    await db.log_spam(1, 456, "spam")
    await db.log_spam(2, 456, "spam")
    count1 = await db.get_spam_count(1, 456, interval_seconds=60)
    count2 = await db.get_spam_count(2, 456, interval_seconds=60)
    assert count1 == 1
    assert count2 == 1


@pytest.mark.asyncio
async def test_get_stats(db):
    await db.init()
    await db.create_user(1, 100)
    await db.create_user(2, 100)
    await db.create_user(3, 100)
    await db.add_warning(2, 100)
    await db.ban_user(3, 100)
    stats = await db.get_stats(100)
    assert stats["total"] == 3
    assert stats["warned"] == 1
    assert stats["banned"] == 1


@pytest.mark.asyncio
async def test_create_user_idempotent(db):
    await db.init()
    await db.create_user(123, 456)
    await db.add_warning(123, 456)
    await db.create_user(123, 456)
    user = await db.get_user(123, 456)
    assert user.warnings == 1
