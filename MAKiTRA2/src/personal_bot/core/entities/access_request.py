from dataclasses import dataclass

from personal_bot.core.enums import AccessRequestStatus


@dataclass(frozen=True)
class AccessRequest:
    id: int
    telegram_id: int
    username: str | None
    first_name: str
    last_name: str | None
    phone_number: str
    status: AccessRequestStatus
    created_at: str
