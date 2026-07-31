from dataclasses import dataclass

from personal_bot.core.enums import UserRole, UserStatus


@dataclass(frozen=True)
class User:
    id: int
    telegram_id: int
    is_bot: bool = False
    username: str | None = None
    first_name: str = ""
    last_name: str | None = None
    full_name: str | None = None
    phone_number: str | None = None
    role: UserRole = UserRole.USER
    status: UserStatus = UserStatus.ACTIVE
    created_at: str | None = None
    updated_at: str | None = None
    last_activity_at: str | None = None
    timezone: str | None = None
    language_code: str | None = None
    is_premium: bool | None = None
    added_to_attachment_menu: bool | None = None
    allows_write_to_pm: bool | None = None
    can_join_groups: bool | None = None
    can_read_all_group_messages: bool | None = None
    supports_inline_queries: bool | None = None
    can_connect_to_business: bool | None = None
    has_main_web_app: bool | None = None
    has_topics_enabled: bool | None = None
    allows_users_to_create_topics: bool | None = None
    can_manage_bots: bool | None = None
    supports_guest_queries: bool | None = None
