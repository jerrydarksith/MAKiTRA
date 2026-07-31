from dataclasses import dataclass
from datetime import datetime, timezone

from personal_bot.core.entities.user import User
from personal_bot.core.enums import UserRole, UserStatus
from personal_bot.db.repositories.user_repository import UserRepository


@dataclass(frozen=True)
class UsersPage:
    page: int
    page_size: int
    total_pages: int
    users: tuple[User, ...]


class UsersService:
    def __init__(self, user_repository: UserRepository) -> None:
        self._user_repository = user_repository

    def find_user_by_telegram_id(self, telegram_id: int) -> User | None:
        return self._user_repository.find_by_telegram_id(telegram_id)

    def find_user_by_id(self, user_id: int) -> User | None:
        return self._user_repository.find_by_id(user_id)

    def get_active_users_count(self) -> int:
        return len(self._user_repository.list_active_users())

    def get_users_page(self, page: int, page_size: int) -> UsersPage:
        normalized_page = max(1, page)
        normalized_page_size = max(1, page_size)
        users = self._user_repository.list_users()
        total_pages = max(1, (len(users) + normalized_page_size - 1) // normalized_page_size)
        current_page = min(normalized_page, total_pages)
        start_index = (current_page - 1) * normalized_page_size
        page_users = tuple(users[start_index:start_index + normalized_page_size])

        return UsersPage(
            page=current_page,
            page_size=normalized_page_size,
            total_pages=total_pages,
            users=page_users,
        )

    def get_active_users_page(self, page: int, page_size: int) -> UsersPage:
        normalized_page = max(1, page)
        normalized_page_size = max(1, page_size)
        active_users = self._user_repository.list_active_users()
        total_pages = max(1, (len(active_users) + normalized_page_size - 1) // normalized_page_size)
        start_index = (normalized_page - 1) * normalized_page_size
        end_index = start_index + normalized_page_size
        page_users = tuple(active_users[start_index:end_index])

        return UsersPage(
            page=normalized_page,
            page_size=normalized_page_size,
            total_pages=total_pages,
            users=page_users,
        )

    def build_users_page_message(self, users_page: UsersPage) -> str:
        lines = ["👥 Користувачі", ""]

        if not users_page.users:
            lines.append("Немає користувачів.")
            return "\n".join(lines)

        lines.append("Оберіть користувача з кнопок нижче.")
        if users_page.total_pages > 1:
            lines.append(f"Сторінка {users_page.page}/{users_page.total_pages}")

        return "\n".join(lines).rstrip()

    def build_user_details_message(self, user: User) -> str:
        lines = ["👤 Інформація про користувача", ""]
        lines.append(f"Telegram ID: {user.telegram_id}")

        detail_pairs: list[tuple[str, str | None]] = [
            ("Ім'я", user.first_name or None),
            ("Прізвище", user.last_name or None),
            ("Нік", user.username or None),
            ("Телефон", user.phone_number or None),
            ("Повне ім'я", user.full_name or None),
            ("Роль", self._translate_role(user.role)),
            ("Статус", self._translate_status(user.status)),
            ("Дата реєстрації", user.created_at or None),
            ("Остання активність", user.last_activity_at or None),
            ("Часовий пояс", user.timezone or None),
            ("Мова", user.language_code or None),
            ("Бот", self._format_bool(user.is_bot)),
        ]

        for label, value in detail_pairs:
            if value:
                lines.append(f"{label}: {value}")

        boolean_details = [
            ("Преміум", user.is_premium),
            ("Додано до меню вкладень", user.added_to_attachment_menu),
            ("Дозволено писати в особисті повідомлення", user.allows_write_to_pm),
            ("Може приєднуватися до груп", user.can_join_groups),
            ("Може читати всі повідомлення в групах", user.can_read_all_group_messages),
            ("Підтримує інлайн-запити", user.supports_inline_queries),
            ("Може підключатися до бізнесу", user.can_connect_to_business),
            ("Має головний вебзастосунок", user.has_main_web_app),
            ("Має підтримку тем", user.has_topics_enabled),
            ("Може створювати теми", user.allows_users_to_create_topics),
            ("Може керувати ботами", user.can_manage_bots),
            ("Підтримує гостьові запити", user.supports_guest_queries),
        ]

        for label, value in boolean_details:
            if value is not None:
                lines.append(f"{label}: {self._format_bool(value)}")

        return "\n".join(lines)

    def build_user_button_label(self, user: User) -> str:
        return self._format_user_label(user)

    def block_user(self, user_id: int) -> User | None:
        user = self.find_user_by_id(user_id)
        if user is None or user.status is UserStatus.BLOCKED:
            return user
        self._user_repository.update_status(user_id, UserStatus.BLOCKED, self._now())
        return self.find_user_by_id(user_id)

    def unblock_user(self, user_id: int) -> User | None:
        user = self.find_user_by_id(user_id)
        if user is None or user.status is UserStatus.ACTIVE:
            return user
        self._user_repository.update_status(user_id, UserStatus.ACTIVE, self._now())
        return self.find_user_by_id(user_id)

    def delete_user(self, user_id: int) -> None:
        self._user_repository.delete_user(user_id)

    def _format_user_label(self, user: User) -> str:
        if user.username:
            phone_suffix = self._shorten_phone(user.phone_number)
            return f"{user.username}/{phone_suffix}" if phone_suffix else user.username

        if user.first_name or user.last_name:
            display_name = " ".join(part for part in (user.first_name, user.last_name) if part).strip()
            phone_suffix = self._shorten_phone(user.phone_number)
            return f"{display_name}/{phone_suffix}" if phone_suffix else display_name

        if user.phone_number:
            return self._shorten_phone(user.phone_number) or user.phone_number

        return str(user.telegram_id)

    @staticmethod
    def _format_bool(value: bool | None) -> str:
        if value is None:
            return "—"
        return "Так" if value else "Ні"

    @staticmethod
    def _translate_role(role: UserRole) -> str:
        translations = {
            UserRole.SUPER_ADMIN: "Супер адміністратор",
            UserRole.ADMIN: "Адміністратор",
            UserRole.USER: "Користувач",
        }
        return translations.get(role, role.value)

    @staticmethod
    def _translate_status(status: UserStatus) -> str:
        translations = {
            UserStatus.ACTIVE: "Активний",
            UserStatus.BLOCKED: "Заблокований",
        }
        return translations.get(status, status.value)

    @staticmethod
    def _shorten_phone(phone_number: str | None) -> str | None:
        if not phone_number:
            return None
        normalized = phone_number.strip()
        if len(normalized) <= 9:
            return normalized
        return f"{normalized[:6]}...{normalized[-3:]}"

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()
