from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Barrier
import unittest

from personal_bot.access.service import AccessService
from personal_bot.core.enums import (
    AccessRequestReviewResult,
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


class AccessRequestReviewTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = TemporaryDirectory()
        self.database_path = Path(self.temporary_directory.name) / "personal_bot.sqlite3"
        self.database = Database(self.database_path)
        initialize_database_schema(self.database)
        self.access_service = self._create_access_service(self.database)
        self.super_admin_telegram_id = 100001
        self.access_service.register_contact(
            telegram_id=self.super_admin_telegram_id,
            username="super_admin",
            first_name="Адмін",
            last_name=None,
            phone_number="+380000000001",
        )

    def tearDown(self) -> None:
        self.database.close()
        self.temporary_directory.cleanup()

    def test_approve_access_request_creates_user_and_settings(self) -> None:
        access_request_id = self._create_pending_access_request(200001)

        review_outcome = self.access_service.approve_access_request(
            access_request_id,
            self.super_admin_telegram_id,
        )
        user = self.access_service.find_user_by_telegram_id(200001)
        access_request_row = self.database.execute(
            """
            SELECT status, reviewed_by_user_id, reviewed_at
            FROM access_requests
            WHERE id = ?
            """,
            (access_request_id,),
        ).fetchone()
        settings_row = self.database.execute(
            "SELECT user_id FROM user_settings WHERE user_id = ?",
            (user.id,),
        ).fetchone()

        self.assertIs(review_outcome.result, AccessRequestReviewResult.APPROVED)
        self.assertIsNotNone(user)
        self.assertIs(user.role, UserRole.USER)
        self.assertIs(user.status, UserStatus.ACTIVE)
        self.assertEqual(access_request_row["status"], AccessRequestStatus.APPROVED.value)
        self.assertIsNotNone(access_request_row["reviewed_by_user_id"])
        self.assertIsNotNone(access_request_row["reviewed_at"])
        self.assertEqual(settings_row["user_id"], user.id)

    def test_reject_access_request_allows_new_registration(self) -> None:
        access_request_id = self._create_pending_access_request(200001)

        review_outcome = self.access_service.reject_access_request(
            access_request_id,
            self.super_admin_telegram_id,
        )
        registration_outcome = self.access_service.register_contact(
            telegram_id=200001,
            username="applicant",
            first_name="Користувач",
            last_name=None,
            phone_number="+380000000002",
        )
        access_request_rows = self.database.execute(
            "SELECT status FROM access_requests WHERE telegram_id = ? ORDER BY id",
            (200001,),
        ).fetchall()

        self.assertIs(review_outcome.result, AccessRequestReviewResult.REJECTED)
        self.assertIs(
            registration_outcome.result,
            ContactRegistrationResult.ACCESS_REQUEST_CREATED,
        )
        self.assertEqual(
            [access_request_row["status"] for access_request_row in access_request_rows],
            [AccessRequestStatus.REJECTED.value, AccessRequestStatus.PENDING.value],
        )

    def test_second_approve_does_not_change_processed_access_request(self) -> None:
        access_request_id = self._create_pending_access_request(200001)
        self.access_service.approve_access_request(
            access_request_id,
            self.super_admin_telegram_id,
        )

        review_outcome = self.access_service.approve_access_request(
            access_request_id,
            self.super_admin_telegram_id,
        )

        self.assertIs(
            review_outcome.result,
            AccessRequestReviewResult.ALREADY_PROCESSED,
        )

    def test_second_reject_does_not_change_processed_access_request(self) -> None:
        access_request_id = self._create_pending_access_request(200001)
        self.access_service.reject_access_request(
            access_request_id,
            self.super_admin_telegram_id,
        )

        review_outcome = self.access_service.reject_access_request(
            access_request_id,
            self.super_admin_telegram_id,
        )

        self.assertIs(
            review_outcome.result,
            AccessRequestReviewResult.ALREADY_PROCESSED,
        )

    def test_two_super_admins_cannot_approve_same_access_request(self) -> None:
        second_super_admin_telegram_id = 100002
        self._create_second_super_admin(second_super_admin_telegram_id)
        access_request_id = self._create_pending_access_request(200001)
        synchronization_barrier = Barrier(2)

        def approve_as_super_admin(
            reviewer_telegram_id: int,
        ) -> AccessRequestReviewResult:
            database = Database(self.database_path)

            try:
                access_service = self._create_access_service(database)
                synchronization_barrier.wait()
                return access_service.approve_access_request(
                    access_request_id,
                    reviewer_telegram_id,
                ).result
            finally:
                database.close()

        with ThreadPoolExecutor(max_workers=2) as executor:
            review_results = list(
                executor.map(
                    approve_as_super_admin,
                    [self.super_admin_telegram_id, second_super_admin_telegram_id],
                )
            )

        self.assertCountEqual(
            review_results,
            [
                AccessRequestReviewResult.APPROVED,
                AccessRequestReviewResult.ALREADY_PROCESSED,
            ],
        )

    def _create_pending_access_request(self, telegram_id: int) -> int:
        registration_outcome = self.access_service.register_contact(
            telegram_id=telegram_id,
            username="applicant",
            first_name="Користувач",
            last_name=None,
            phone_number="+380000000002",
        )

        self.assertIs(
            registration_outcome.result,
            ContactRegistrationResult.ACCESS_REQUEST_CREATED,
        )
        self.assertIsNotNone(registration_outcome.access_request)
        return registration_outcome.access_request.id

    def _create_second_super_admin(self, telegram_id: int) -> None:
        with self.database.transaction():
            UserRepository(self.database).create(
                telegram_id=telegram_id,
                username="second_super_admin",
                first_name="Другий адмін",
                last_name=None,
                phone_number="+380000000003",
                role=UserRole.SUPER_ADMIN,
                status=UserStatus.ACTIVE,
                created_at="2026-01-01T00:00:00+00:00",
            )

    @staticmethod
    def _create_access_service(database: Database) -> AccessService:
        return AccessService(
            database,
            UserRepository(database),
            SettingsRepository(database),
            AccessRequestRepository(database),
        )


if __name__ == "__main__":
    unittest.main()
