from dataclasses import dataclass

from personal_bot.core.enums import UserRole, UserStatus


@dataclass(frozen=True)
class User:
    id: int
    telegram_id: int
    username: str | None
    first_name: str
    last_name: str | None
    role: UserRole
    status: UserStatus
