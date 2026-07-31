from personal_bot.core.entities.access_request import AccessRequest
from personal_bot.core.enums import AccessRequestStatus
from personal_bot.db.database import Database


class AccessRequestRepository:
    def __init__(self, database: Database) -> None:
        self._database = database

    def create_pending(
        self,
        telegram_id: int,
        username: str | None,
        first_name: str,
        last_name: str | None,
        phone_number: str,
        created_at: str,
        is_bot: bool = False,
        full_name: str | None = None,
        language_code: str | None = None,
        is_premium: bool | None = None,
        added_to_attachment_menu: bool | None = None,
        can_join_groups: bool | None = None,
        can_read_all_group_messages: bool | None = None,
        supports_inline_queries: bool | None = None,
        can_connect_to_business: bool | None = None,
        has_main_web_app: bool | None = None,
        has_topics_enabled: bool | None = None,
        allows_users_to_create_topics: bool | None = None,
        can_manage_bots: bool | None = None,
        supports_guest_queries: bool | None = None,
    ) -> AccessRequest:
        cursor = self._database.execute(
            """
            INSERT INTO access_requests (
                telegram_id,
                is_bot,
                username,
                first_name,
                last_name,
                full_name,
                phone_number,
                language_code,
                is_premium,
                added_to_attachment_menu,
                can_join_groups,
                can_read_all_group_messages,
                supports_inline_queries,
                can_connect_to_business,
                has_main_web_app,
                has_topics_enabled,
                allows_users_to_create_topics,
                can_manage_bots,
                supports_guest_queries,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                telegram_id,
                1 if is_bot else 0,
                username,
                first_name,
                last_name,
                full_name,
                phone_number,
                language_code,
                self._bool_to_int(is_premium),
                self._bool_to_int(added_to_attachment_menu),
                self._bool_to_int(can_join_groups),
                self._bool_to_int(can_read_all_group_messages),
                self._bool_to_int(supports_inline_queries),
                self._bool_to_int(can_connect_to_business),
                self._bool_to_int(has_main_web_app),
                self._bool_to_int(has_topics_enabled),
                self._bool_to_int(allows_users_to_create_topics),
                self._bool_to_int(can_manage_bots),
                self._bool_to_int(supports_guest_queries),
                AccessRequestStatus.PENDING.value,
                created_at,
            ),
        )
        return AccessRequest(
            id=cursor.lastrowid,
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            status=AccessRequestStatus.PENDING,
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

    def has_pending_for_telegram_id(self, telegram_id: int) -> bool:
        access_request_row = self._database.execute(
            """
            SELECT 1
            FROM access_requests
            WHERE telegram_id = ? AND status = ?
            LIMIT 1
            """,
            (telegram_id, AccessRequestStatus.PENDING.value),
        ).fetchone()
        return access_request_row is not None

    def find_by_id(self, access_request_id: int) -> AccessRequest | None:
        access_request_row = self._database.execute(
            """
                 SELECT id, telegram_id, is_bot, username, first_name, last_name, full_name,
                     phone_number, language_code, is_premium, added_to_attachment_menu,
                     can_join_groups, can_read_all_group_messages, supports_inline_queries,
                     can_connect_to_business, has_main_web_app, has_topics_enabled,
                     allows_users_to_create_topics, can_manage_bots, supports_guest_queries,
                     status, created_at
            FROM access_requests
            WHERE id = ?
            """,
            (access_request_id,),
        ).fetchone()

        if access_request_row is None:
            return None

        return AccessRequest(
            id=access_request_row["id"],
            telegram_id=access_request_row["telegram_id"],
            username=access_request_row["username"],
            first_name=access_request_row["first_name"],
            last_name=access_request_row["last_name"],
            phone_number=access_request_row["phone_number"],
            status=AccessRequestStatus(access_request_row["status"]),
            created_at=access_request_row["created_at"],
            is_bot=bool(access_request_row["is_bot"]),
            full_name=access_request_row["full_name"],
            language_code=access_request_row["language_code"],
            is_premium=self._int_to_bool(access_request_row["is_premium"]),
            added_to_attachment_menu=self._int_to_bool(access_request_row["added_to_attachment_menu"]),
            can_join_groups=self._int_to_bool(access_request_row["can_join_groups"]),
            can_read_all_group_messages=self._int_to_bool(access_request_row["can_read_all_group_messages"]),
            supports_inline_queries=self._int_to_bool(access_request_row["supports_inline_queries"]),
            can_connect_to_business=self._int_to_bool(access_request_row["can_connect_to_business"]),
            has_main_web_app=self._int_to_bool(access_request_row["has_main_web_app"]),
            has_topics_enabled=self._int_to_bool(access_request_row["has_topics_enabled"]),
            allows_users_to_create_topics=self._int_to_bool(access_request_row["allows_users_to_create_topics"]),
            can_manage_bots=self._int_to_bool(access_request_row["can_manage_bots"]),
            supports_guest_queries=self._int_to_bool(access_request_row["supports_guest_queries"]),
        )

    def mark_reviewed(
        self,
        access_request_id: int,
        status: AccessRequestStatus,
        reviewed_by_user_id: int,
        reviewed_at: str,
    ) -> None:
        self._database.execute(
            """
            UPDATE access_requests
            SET status = ?, reviewed_by_user_id = ?, reviewed_at = ?
            WHERE id = ?
            """,
            (
                status.value,
                reviewed_by_user_id,
                reviewed_at,
                access_request_id,
            ),
        )

    @staticmethod
    def _bool_to_int(value: bool | None) -> int | None:
        return 1 if value is True else 0 if value is False else None

    @staticmethod
    def _int_to_bool(value: int | None) -> bool | None:
        return None if value is None else bool(value)
