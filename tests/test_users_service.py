from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from personal_bot.core.enums import UserRole, UserStatus
from personal_bot.db.database import Database
from personal_bot.db.repositories.user_repository import UserRepository
from personal_bot.db.schema import initialize_database_schema
from personal_bot.users.service import UsersService


class UsersServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = TemporaryDirectory()
        self.database_path = Path(self.temporary_directory.name) / "personal_bot.sqlite3"
        self.database = Database(self.database_path)
        initialize_database_schema(self.database)
        self.user_repository = UserRepository(self.database)
        self.users_service = UsersService(self.user_repository)

    def tearDown(self) -> None:
        self.database.close()
        self.temporary_directory.cleanup()

    def test_get_active_users_page_returns_only_active_users_with_pagination(self) -> None:
        self._create_user(100001, "first_admin", "Перший", None, UserRole.SUPER_ADMIN, UserStatus.ACTIVE)
        self._create_user(100002, "blocked_user", "Блокований", None, UserRole.USER, UserStatus.BLOCKED)
        self._create_user(100003, "second_user", "Другий", None, UserRole.USER, UserStatus.ACTIVE)
        self._create_user(100004, "third_user", "Третій", None, UserRole.USER, UserStatus.ACTIVE)

        page = self.users_service.get_active_users_page(page=1, page_size=2)

        self.assertEqual(page.page, 1)
        self.assertEqual(page.page_size, 2)
        self.assertEqual(page.total_pages, 2)
        self.assertEqual(len(page.users), 2)
        self.assertEqual(
            {user.telegram_id for user in page.users},
            {100001, 100003},
        )

    def _create_user(
        self,
        telegram_id: int,
        username: str,
        first_name: str,
        last_name: str | None,
        role: UserRole,
        status: UserStatus,
    ) -> None:
        self.user_repository.create(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            phone_number=f"+380000000{telegram_id}",
            role=role,
            status=status,
            created_at="2026-01-01T00:00:00+00:00",
        )


if __name__ == "__main__":
    unittest.main()
