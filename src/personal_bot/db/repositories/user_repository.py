from personal_bot.core.entities.user import User
from personal_bot.core.enums import UserRole, UserStatus
from personal_bot.db.database import Database


class UserRepository:
    def __init__(self, database: Database) -> None:
        self._database = database

    def find_by_telegram_id(self, telegram_id: int) -> User | None:
        user_row = self._database.execute(
            """
            SELECT id, telegram_id, is_bot, username, first_name, last_name, full_name, phone_number,
                   role, status, created_at, updated_at, last_activity_at, timezone,
                   language_code, is_premium, added_to_attachment_menu,
                   allows_write_to_pm, can_join_groups, can_read_all_group_messages,
                   supports_inline_queries, can_connect_to_business, has_main_web_app,
                   has_topics_enabled, allows_users_to_create_topics, can_manage_bots,
                   supports_guest_queries
            FROM users
            WHERE telegram_id = ?
            """,
            (telegram_id,),
        ).fetchone()

        if user_row is None:
            return None

        return self._row_to_user(user_row)

    def find_by_id(self, user_id: int) -> User | None:
        user_row = self._database.execute(
            """
            SELECT id, telegram_id, is_bot, username, first_name, last_name, full_name, phone_number,
                   role, status, created_at, updated_at, last_activity_at, timezone,
                   language_code, is_premium, added_to_attachment_menu,
                   allows_write_to_pm, can_join_groups, can_read_all_group_messages,
                   supports_inline_queries, can_connect_to_business, has_main_web_app,
                   has_topics_enabled, allows_users_to_create_topics, can_manage_bots,
                   supports_guest_queries
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        ).fetchone()

        if user_row is None:
            return None

        return self._row_to_user(user_row)

    def has_any_users(self) -> bool:
        user_row = self._database.execute("SELECT 1 FROM users LIMIT 1").fetchone()
        return user_row is not None

    def create(
        self,
        telegram_id: int,
        username: str | None,
        first_name: str,
        last_name: str | None,
        phone_number: str | None,
        role: UserRole,
        status: UserStatus,
        created_at: str,
        is_bot: bool = False,
        full_name: str | None = None,
        updated_at: str | None = None,
        last_activity_at: str | None = None,
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
    ) -> int:
        cursor = self._database.execute(
            """
            INSERT INTO users (
                telegram_id,
                is_bot,
                username,
                first_name,
                last_name,
                full_name,
                phone_number,
                role,
                status,
                created_at,
                updated_at,
                last_activity_at,
                timezone,
                language_code,
                is_premium,
                added_to_attachment_menu,
                allows_write_to_pm,
                can_join_groups,
                can_read_all_group_messages,
                supports_inline_queries,
                can_connect_to_business,
                has_main_web_app,
                has_topics_enabled,
                allows_users_to_create_topics,
                can_manage_bots,
                supports_guest_queries
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                telegram_id,
                1 if is_bot else 0,
                username,
                first_name,
                last_name,
                full_name,
                phone_number,
                role.value,
                status.value,
                created_at,
                updated_at or created_at,
                last_activity_at,
                timezone,
                language_code,
                1 if is_premium is True else 0 if is_premium is False else None,
                1 if added_to_attachment_menu is True else 0 if added_to_attachment_menu is False else None,
                1 if allows_write_to_pm is True else 0 if allows_write_to_pm is False else None,
                1 if can_join_groups is True else 0 if can_join_groups is False else None,
                1 if can_read_all_group_messages is True else 0 if can_read_all_group_messages is False else None,
                1 if supports_inline_queries is True else 0 if supports_inline_queries is False else None,
                1 if can_connect_to_business is True else 0 if can_connect_to_business is False else None,
                1 if has_main_web_app is True else 0 if has_main_web_app is False else None,
                1 if has_topics_enabled is True else 0 if has_topics_enabled is False else None,
                1 if allows_users_to_create_topics is True else 0 if allows_users_to_create_topics is False else None,
                1 if can_manage_bots is True else 0 if can_manage_bots is False else None,
                1 if supports_guest_queries is True else 0 if supports_guest_queries is False else None,
            ),
        )
        return cursor.lastrowid

    def find_active_super_admins(self) -> list[User]:
        user_rows = self._database.execute(
            """
            SELECT id, telegram_id, is_bot, username, first_name, last_name, full_name, phone_number,
                   role, status, created_at, updated_at, last_activity_at, timezone,
                   language_code, is_premium, added_to_attachment_menu,
                   allows_write_to_pm, can_join_groups, can_read_all_group_messages,
                   supports_inline_queries, can_connect_to_business, has_main_web_app,
                   has_topics_enabled, allows_users_to_create_topics, can_manage_bots,
                   supports_guest_queries
            FROM users
            WHERE role = ? AND status = ?
            """,
            (UserRole.SUPER_ADMIN.value, UserStatus.ACTIVE.value),
        ).fetchall()

        return [self._row_to_user(user_row) for user_row in user_rows]

    def list_active_users(self) -> list[User]:
        user_rows = self._database.execute(
            """
            SELECT id, telegram_id, is_bot, username, first_name, last_name, full_name, phone_number,
                   role, status, created_at, updated_at, last_activity_at, timezone,
                   language_code, is_premium, added_to_attachment_menu,
                   allows_write_to_pm, can_join_groups, can_read_all_group_messages,
                   supports_inline_queries, can_connect_to_business, has_main_web_app,
                   has_topics_enabled, allows_users_to_create_topics, can_manage_bots,
                   supports_guest_queries
            FROM users
            WHERE status = ?
            ORDER BY first_name COLLATE NOCASE, last_name COLLATE NOCASE, username COLLATE NOCASE
            """,
            (UserStatus.ACTIVE.value,),
        ).fetchall()

        return [self._row_to_user(user_row) for user_row in user_rows]

    def list_users(self) -> list[User]:
        user_rows = self._database.execute(
            """
            SELECT id, telegram_id, is_bot, username, first_name, last_name, full_name, phone_number,
                   role, status, created_at, updated_at, last_activity_at, timezone,
                   language_code, is_premium, added_to_attachment_menu,
                   allows_write_to_pm, can_join_groups, can_read_all_group_messages,
                   supports_inline_queries, can_connect_to_business, has_main_web_app,
                   has_topics_enabled, allows_users_to_create_topics, can_manage_bots,
                   supports_guest_queries
            FROM users
            ORDER BY first_name COLLATE NOCASE, last_name COLLATE NOCASE, username COLLATE NOCASE
            """
        ).fetchall()
        return [self._row_to_user(user_row) for user_row in user_rows]

    def update_status(self, user_id: int, status: UserStatus, updated_at: str) -> None:
        self._database.execute(
            "UPDATE users SET status = ?, updated_at = ? WHERE id = ?",
            (status.value, updated_at, user_id),
        )

    def update_telegram_profile(
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
        full_name: str | None,
        phone_number: str | None,
        last_activity_at: str,
    ) -> None:
        self._database.execute(
            """
            UPDATE users
            SET is_bot = ?, username = ?, first_name = ?, last_name = ?,
                full_name = ?, phone_number = COALESCE(?, phone_number),
                language_code = ?, is_premium = ?, added_to_attachment_menu = ?,
                can_join_groups = ?, can_read_all_group_messages = ?,
                supports_inline_queries = ?, can_connect_to_business = ?,
                has_main_web_app = ?, has_topics_enabled = ?,
                allows_users_to_create_topics = ?, can_manage_bots = ?,
                supports_guest_queries = ?, last_activity_at = ?, updated_at = ?
            WHERE telegram_id = ?
            """,
            (
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
                last_activity_at,
                last_activity_at,
                telegram_id,
            ),
        )

    def delete_user(self, user_id: int) -> None:
        with self._database.transaction():
            self._database.execute(
                "UPDATE access_requests SET reviewed_by_user_id = NULL WHERE reviewed_by_user_id = ?",
                (user_id,),
            )
            self._database.execute("DELETE FROM users WHERE id = ?", (user_id,))

    @staticmethod
    def _bool_to_int(value: bool | None) -> int | None:
        return 1 if value is True else 0 if value is False else None

    @staticmethod
    def _row_to_user(user_row) -> User:
        return User(
            id=user_row["id"],
            telegram_id=user_row["telegram_id"],
            is_bot=bool(user_row["is_bot"]),
            username=user_row["username"],
            first_name=user_row["first_name"] or "",
            last_name=user_row["last_name"],
            full_name=user_row["full_name"],
            phone_number=user_row["phone_number"],
            role=UserRole(user_row["role"]),
            status=UserStatus(user_row["status"]),
            created_at=user_row["created_at"],
            updated_at=user_row["updated_at"],
            last_activity_at=user_row["last_activity_at"],
            timezone=user_row["timezone"],
            language_code=user_row["language_code"],
            is_premium=bool(user_row["is_premium"]) if user_row["is_premium"] is not None else None,
            added_to_attachment_menu=(
                bool(user_row["added_to_attachment_menu"])
                if user_row["added_to_attachment_menu"] is not None
                else None
            ),
            allows_write_to_pm=(
                bool(user_row["allows_write_to_pm"])
                if user_row["allows_write_to_pm"] is not None
                else None
            ),
            can_join_groups=(
                bool(user_row["can_join_groups"])
                if user_row["can_join_groups"] is not None
                else None
            ),
            can_read_all_group_messages=(
                bool(user_row["can_read_all_group_messages"])
                if user_row["can_read_all_group_messages"] is not None
                else None
            ),
            supports_inline_queries=(
                bool(user_row["supports_inline_queries"])
                if user_row["supports_inline_queries"] is not None
                else None
            ),
            can_connect_to_business=(
                bool(user_row["can_connect_to_business"])
                if user_row["can_connect_to_business"] is not None
                else None
            ),
            has_main_web_app=(
                bool(user_row["has_main_web_app"])
                if user_row["has_main_web_app"] is not None
                else None
            ),
            has_topics_enabled=(
                bool(user_row["has_topics_enabled"])
                if user_row["has_topics_enabled"] is not None
                else None
            ),
            allows_users_to_create_topics=(
                bool(user_row["allows_users_to_create_topics"])
                if user_row["allows_users_to_create_topics"] is not None
                else None
            ),
            can_manage_bots=(
                bool(user_row["can_manage_bots"])
                if user_row["can_manage_bots"] is not None
                else None
            ),
            supports_guest_queries=(
                bool(user_row["supports_guest_queries"])
                if user_row["supports_guest_queries"] is not None
                else None
            ),
        )