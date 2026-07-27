from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from personal_bot.access.service import AccessService
from personal_bot.core.enums import (
    AccessRequestStatus,
    ContactRegistrationResult,
    UserRole,
    UserStatus,
)
from personal_bot.db.database import Database
from personal_bot.db.repositories.access_request_repository import AccessRequestRepository
from personal_bot.db.repositories.settings_repository import SettingsRepository
from personal_bot.db.repositories.user_repository import UserRepository
from personal_bot.db.schema import initialize_database_schema


class AccessServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = TemporaryDirectory()
        database_path = Path(self.temporary_directory.name) / "personal_bot.sqlite3"
        self.database = Database(database_path)
        initialize_database_schema(self.database)
        self.access_service = AccessService(
            self.database,
            UserRepository(self.database),
            SettingsRepository(self.database),
            AccessRequestRepository(self.database),
        )

    def tearDown(self) -> None:
        self.database.close()
        self.temporary_directory.cleanup()

    def test_register_contact_creates_first_super_admin_and_settings(self) -> None:
        registration_outcome = self.access_service.register_contact(
            telegram_id=123456,
            username="username",
            first_name="Ім'я",
            last_name=None,
            phone_number="+380000000000",
        )
        user = self.access_service.find_user_by_telegram_id(123456)
        settings_row = self.database.execute(
            "SELECT timezone, currency, date_format, language FROM user_settings"
        ).fetchone()

        self.assertIs(
            registration_outcome.result,
            ContactRegistrationResult.FIRST_SUPER_ADMIN_CREATED,
        )
        self.assertIsNotNone(user)
        self.assertIs(user.role, UserRole.SUPER_ADMIN)
        self.assertIs(user.status, UserStatus.ACTIVE)
        self.assertEqual(settings_row["timezone"], "Europe/Kyiv")
        self.assertEqual(settings_row["currency"], "UAH")
        self.assertEqual(settings_row["date_format"], "DD.MM.YYYY")
        self.assertEqual(settings_row["language"], "uk")

    def test_register_contact_creates_pending_access_request_for_next_user(self) -> None:
        self.access_service.register_contact(
            telegram_id=123456,
            username="first_user",
            first_name="Перший",
            last_name=None,
            phone_number="+380000000000",
        )

        registration_outcome = self.access_service.register_contact(
            telegram_id=654321,
            username="next_user",
            first_name="Наступний",
            last_name=None,
            phone_number="+380000000001",
        )
        access_request_row = self.database.execute(
            "SELECT telegram_id, status FROM access_requests"
        ).fetchone()

        self.assertIs(
            registration_outcome.result,
            ContactRegistrationResult.ACCESS_REQUEST_CREATED,
        )
        self.assertEqual(access_request_row["telegram_id"], 654321)
        self.assertEqual(
            access_request_row["status"],
            AccessRequestStatus.PENDING.value,
        )
        self.assertEqual(len(registration_outcome.super_admins), 1)
        self.assertEqual(
            registration_outcome.super_admins[0].telegram_id,
            123456,
        )

    def test_register_contact_does_not_create_duplicate_pending_access_request(self) -> None:
        self.access_service.register_contact(
            telegram_id=123456,
            username="first_user",
            first_name="Перший",
            last_name=None,
            phone_number="+380000000000",
        )
        self.access_service.register_contact(
            telegram_id=654321,
            username="next_user",
            first_name="Наступний",
            last_name=None,
            phone_number="+380000000001",
        )

        registration_outcome = self.access_service.register_contact(
            telegram_id=654321,
            username="next_user",
            first_name="Наступний",
            last_name=None,
            phone_number="+380000000001",
        )
        access_request_row = self.database.execute(
            "SELECT COUNT(*) AS count FROM access_requests"
        ).fetchone()

        self.assertIs(
            registration_outcome.result,
            ContactRegistrationResult.ACCESS_REQUEST_ALREADY_PENDING,
        )
        self.assertEqual(access_request_row["count"], 1)

    def test_find_user_by_telegram_id_returns_none_for_unknown_user(self) -> None:
        user = self.access_service.find_user_by_telegram_id(123456)

        self.assertIsNone(user)


if __name__ == "__main__":
    unittest.main()
