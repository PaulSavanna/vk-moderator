from dataclasses import dataclass


@dataclass
class User:
    user_id: int
    chat_id: int
    warnings: int = 0
    is_banned: bool = False
    captcha_passed: bool = False
