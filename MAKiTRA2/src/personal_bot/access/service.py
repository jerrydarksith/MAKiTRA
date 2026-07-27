from datetime import datetime, timezone
from dataclasses import dataclass

from personal_bot.core.entities.access_request import AccessRequest
from personal_bot.core.entities.user import User
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


@dataclass(frozen=True)
class ContactRegistrationOutcome:
    result: ContactRegistrationResult
    access_request: AccessRequest | None = None
    super_admins: tuple[User, ...] = ()


@dataclass(frozen=True)
class AccessRequestReviewOutcome:
    result: AccessRequestReviewResult
    access_request: AccessRequest | None = None


class AccessService:
    def __init__(
        self,
        database: Database,
        user_repository: UserRepository,
        settings_repository: SettingsRepository,
        access_request_repository: AccessRequestRepository,
    ) -> None:
        self._database = database
        self._user_repository = user_repository
        self._settings_repository = settings_repository
        self._access_request_repository = access_request_repository

    def find_user_by_telegram_id(self, telegram_id: int) -> User | None:
        return self._user_repository.find_by_telegram_id(telegram_id)

    def register_contact(
        self,
        telegram_id: int,
        username: str | None,
        first_name: str,
        last_name: str | None,
        phone_number: str,
    ) -> ContactRegistrationOutcome:
        created_at = self._get_current_timestamp()

        with self._database.transaction():
            existing_user = self._user_repository.find_by_telegram_id(telegram_id)

            if existing_user is not None:
                return ContactRegistrationOutcome(
                    result=ContactRegistrationResult.USER_ALREADY_REGISTERED
                )

            if not self._user_repository.has_any_users():
                user_id = self._user_repository.create(
                    telegram_id=telegram_id,
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    phone_number=phone_number,
                    role=UserRole.SUPER_ADMIN,
                    status=UserStatus.ACTIVE,
                    created_at=created_at,
                )
                self._settings_repository.create_default(user_id, created_at)
                return ContactRegistrationOutcome(
                    result=ContactRegistrationResult.FIRST_SUPER_ADMIN_CREATED
                )

            if self._access_request_repository.has_pending_for_telegram_id(telegram_id):
                return ContactRegistrationOutcome(
                    result=ContactRegistrationResult.ACCESS_REQUEST_ALREADY_PENDING
                )

            access_request = self._access_request_repository.create_pending(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                phone_number=phone_number,
                created_at=created_at,
            )
            super_admins = self._user_repository.find_active_super_admins()
            return ContactRegistrationOutcome(
                result=ContactRegistrationResult.ACCESS_REQUEST_CREATED,
                access_request=access_request,
                super_admins=tuple(super_admins),
            )

    def approve_access_request(
        self,
        access_request_id: int,
        reviewer_telegram_id: int,
    ) -> AccessRequestReviewOutcome:
        with self._database.transaction():
            reviewer = self._user_repository.find_by_telegram_id(reviewer_telegram_id)

            if not self._is_active_super_admin(reviewer):
                return AccessRequestReviewOutcome(
                    result=AccessRequestReviewResult.UNAUTHORIZED
                )

            access_request = self._access_request_repository.find_by_id(access_request_id)

            if access_request is None:
                return AccessRequestReviewOutcome(
                    result=AccessRequestReviewResult.NOT_FOUND
                )

            if access_request.status is not AccessRequestStatus.PENDING:
                return AccessRequestReviewOutcome(
                    result=AccessRequestReviewResult.ALREADY_PROCESSED,
                    access_request=access_request,
                )

            reviewed_at = self._get_current_timestamp()
            user_id = self._user_repository.create(
                telegram_id=access_request.telegram_id,
                username=access_request.username,
                first_name=access_request.first_name,
                last_name=access_request.last_name,
                phone_number=access_request.phone_number,
                role=UserRole.USER,
                status=UserStatus.ACTIVE,
                created_at=reviewed_at,
            )
            self._settings_repository.create_default(user_id, reviewed_at)
            self._access_request_repository.mark_reviewed(
                access_request_id=access_request.id,
                status=AccessRequestStatus.APPROVED,
                reviewed_by_user_id=reviewer.id,
                reviewed_at=reviewed_at,
            )
            return AccessRequestReviewOutcome(
                result=AccessRequestReviewResult.APPROVED,
                access_request=access_request,
            )

    def reject_access_request(
        self,
        access_request_id: int,
        reviewer_telegram_id: int,
    ) -> AccessRequestReviewOutcome:
        with self._database.transaction():
            reviewer = self._user_repository.find_by_telegram_id(reviewer_telegram_id)

            if not self._is_active_super_admin(reviewer):
                return AccessRequestReviewOutcome(
                    result=AccessRequestReviewResult.UNAUTHORIZED
                )

            access_request = self._access_request_repository.find_by_id(access_request_id)

            if access_request is None:
                return AccessRequestReviewOutcome(
                    result=AccessRequestReviewResult.NOT_FOUND
                )

            if access_request.status is not AccessRequestStatus.PENDING:
                return AccessRequestReviewOutcome(
                    result=AccessRequestReviewResult.ALREADY_PROCESSED,
                    access_request=access_request,
                )

            self._access_request_repository.mark_reviewed(
                access_request_id=access_request.id,
                status=AccessRequestStatus.REJECTED,
                reviewed_by_user_id=reviewer.id,
                reviewed_at=self._get_current_timestamp(),
            )
            return AccessRequestReviewOutcome(
                result=AccessRequestReviewResult.REJECTED,
                access_request=access_request,
            )

    @staticmethod
    def _is_active_super_admin(user: User | None) -> bool:
        return (
            user is not None
            and user.role is UserRole.SUPER_ADMIN
            and user.status is UserStatus.ACTIVE
        )

    @staticmethod
    def _get_current_timestamp() -> str:
        return datetime.now(timezone.utc).isoformat()
