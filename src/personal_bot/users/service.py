from dataclasses import dataclass

from personal_bot.core.entities.user import User
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

    def get_active_users_count(self) -> int:
        return len(self._user_repository.list_active_users())

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
            lines.append("Немає активних користувачів.")
            return "\n".join(lines)

        for index, user in enumerate(users_page.users, start=1):
            full_name = " ".join(
                part for part in (user.first_name, user.last_name) if part
            )
            display_name = full_name or user.username or "Без імені"
            lines.append(f"{index}. {display_name}")
            lines.append(f"   роль: {user.role.value}")
            lines.append(f"   статус: {user.status.value}")
            lines.append("")

        if users_page.total_pages > 1:
            lines.append(f"Сторінка {users_page.page}/{users_page.total_pages}")

        return "\n".join(lines).rstrip()
