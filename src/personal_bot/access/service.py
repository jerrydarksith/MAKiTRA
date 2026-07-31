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

    def get_registration_mode(self) -> str:
        return self._settings_repository.get_registration_mode()

    def set_registration_mode(self, registration_mode: str) -> None:
        self._settings_repository.set_registration_mode(registration_mode)

    def get_notify_new_users(self) -> bool:
        return self._settings_repository.get_notify_new_users()

    def set_notify_new_users(self, enabled: bool) -> None:
        self._settings_repository.set_notify_new_users(enabled)

    def sync_user_profile(
        self,
        telegram_id: int,
        *,
        is_bot: bool,
        username: str | None,
        first_name: str,
        last_name: str | None,
        language_code: str | None,
        is_premium: bool | None,
        added_to_attachment_menu: bool | None,
        can_join_groups: bool | None,
        can_read_all_group_messages: bool | None,
        supports_inline_queries: bool | None,
        can_connect_to_business: bool | None,
        has_main_web_app: bool | None,
        has_topics_enabled: bool | None,
        allows_users_to_create_topics: bool | None,
        can_manage_bots: bool | None,
        supports_guest_queries: bool | None,
        phone_number: str | None = None,
    ) -> None:
        now = self._get_current_timestamp()
        full_name = " ".join(part for part in (first_name, last_name) if part) or None
        self._user_repository.update_telegram_profile(
            telegram_id,
            is_bot=is_bot,
            username=username,
            first_name=first_name,
            last_name=last_name,
            language_code=language_code,
            is_premium=is_premium,
            added_to_attachment_menu=added_to_attachment_menu,
            can_join_groups=can_join_groups,
            can_read_all_group_messages=can_read_all_group_messages,
            supports_inline_queries=supports_inline_queries,
            can_connect_to_business=can_connect_to_business,
            has_main_web_app=has_main_web_app,
            has_topics_enabled=has_topics_enabled,
            allows_users_to_create_topics=allows_users_to_create_topics,
            can_manage_bots=can_manage_bots,
            supports_guest_queries=supports_guest_queries,
            full_name=full_name,
            phone_number=phone_number,
            last_activity_at=now,
        )

    def register_contact(
        self,
        telegram_id: int,
        username: str | None,
        first_name: str,
        last_name: str | None,
        phone_number: str,
        is_bot: bool = False,
        full_name: str | None = None,
        timezone: str | None = None,
        language_code: str | None = None,
        is_premium: bool | None = None,
        added_to_attachment_menu: bool | None = None,
        allows_write_to_pm: bool | None = None,
        can_join_groups: bool | None = None,
        can_read_all_group_messages: bool | None = None,
        supports_inline_queries: bool | None = None,
        can_connect_to_business: bool | None = None,
        has_main_web_app: bool | None = None,
        has_topics_enabled: bool | None = None,
        allows_users_to_create_topics: bool | None = None,
        can_manage_bots: bool | None = None,
        supports_guest_queries: bool | None = None,
    ) -> ContactRegistrationOutcome:
        created_at = self._get_current_timestamp()

        with self._database.transaction():
            existing_user = self._user_repository.find_by_telegram_id(telegram_id)

            if existing_user is not None:
                self.sync_user_profile(
                    telegram_id,
                    is_bot=is_bot,
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    language_code=language_code,
                    is_premium=is_premium,
                    added_to_attachment_menu=added_to_attachment_menu,
                    can_join_groups=can_join_groups,
                    can_read_all_group_messages=can_read_all_group_messages,
                    supports_inline_queries=supports_inline_queries,
                    can_connect_to_business=can_connect_to_business,
                    has_main_web_app=has_main_web_app,
                    has_topics_enabled=has_topics_enabled,
                    allows_users_to_create_topics=allows_users_to_create_topics,
                    can_manage_bots=can_manage_bots,
                    supports_guest_queries=supports_guest_queries,
                    phone_number=phone_number,
                )
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
                    last_activity_at=created_at,
                    is_bot=is_bot,
                    full_name=full_name,
                    timezone=timezone,
                    language_code=language_code,
                    is_premium=is_premium,
                    added_to_attachment_menu=added_to_attachment_menu,
                    allows_write_to_pm=allows_write_to_pm,
                    can_join_groups=can_join_groups,
                    can_read_all_group_messages=can_read_all_group_messages,
                    supports_inline_queries=supports_inline_queries,
                    can_connect_to_business=can_connect_to_business,
                    has_main_web_app=has_main_web_app,
                    allows_users_to_create_topics=allows_users_to_create_topics,
                    can_manage_bots=can_manage_bots,
                    supports_guest_queries=supports_guest_queries,
                )
                self._settings_repository.create_default(user_id, created_at)
                return ContactRegistrationOutcome(
                    result=ContactRegistrationResult.FIRST_SUPER_ADMIN_CREATED
                )

            if self._access_request_repository.has_pending_for_telegram_id(telegram_id):
                return ContactRegistrationOutcome(
                    result=ContactRegistrationResult.ACCESS_REQUEST_ALREADY_PENDING
                )

            registration_mode = self._settings_repository.get_registration_mode()
            if registration_mode == "automatic":
                user_id = self._user_repository.create(
                    telegram_id=telegram_id,
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    phone_number=phone_number,
                    role=UserRole.USER,
                    status=UserStatus.ACTIVE,
                    created_at=created_at,
                    last_activity_at=created_at,
                    is_bot=is_bot,
                    full_name=full_name,
                    timezone=timezone,
                    language_code=language_code,
                    is_premium=is_premium,
                    added_to_attachment_menu=added_to_attachment_menu,
                    allows_write_to_pm=allows_write_to_pm,
                    can_join_groups=can_join_groups,
                    can_read_all_group_messages=can_read_all_group_messages,
                    supports_inline_queries=supports_inline_queries,
                    can_connect_to_business=can_connect_to_business,
                    has_main_web_app=has_main_web_app,
                    allows_users_to_create_topics=allows_users_to_create_topics,
                    can_manage_bots=can_manage_bots,
                    supports_guest_queries=supports_guest_queries,
                )
                self._settings_repository.create_default(user_id, created_at)
                super_admins = self._user_repository.find_active_super_admins()
                return ContactRegistrationOutcome(
                    result=ContactRegistrationResult.AUTOMATIC_REGISTRATION_COMPLETED,
                    super_admins=tuple(super_admins),
                )

            access_request = self._access_request_repository.create_pending(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                phone_number=phone_number,
                created_at=created_at,
                is_bot=is_bot,
                full_name=full_name,
                language_code=language_code,
                is_premium=is_premium,
                added_to_attachment_menu=added_to_attachment_menu,
                can_join_groups=can_join_groups,
                can_read_all_group_messages=can_read_all_group_messages,
                supports_inline_queries=supports_inline_queries,
                can_connect_to_business=can_connect_to_business,
                has_main_web_app=has_main_web_app,
                has_topics_enabled=has_topics_enabled,
                allows_users_to_create_topics=allows_users_to_create_topics,
                can_manage_bots=can_manage_bots,
                supports_guest_queries=supports_guest_queries,
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
                is_bot=access_request.is_bot,
                full_name=access_request.full_name,
                language_code=access_request.language_code,
                is_premium=access_request.is_premium,
                added_to_attachment_menu=access_request.added_to_attachment_menu,
                can_join_groups=access_request.can_join_groups,
                can_read_all_group_messages=access_request.can_read_all_group_messages,
                supports_inline_queries=access_request.supports_inline_queries,
                can_connect_to_business=access_request.can_connect_to_business,
                has_main_web_app=access_request.has_main_web_app,
                has_topics_enabled=access_request.has_topics_enabled,
                allows_users_to_create_topics=access_request.allows_users_to_create_topics,
                can_manage_bots=access_request.can_manage_bots,
                supports_guest_queries=access_request.supports_guest_queries,
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
