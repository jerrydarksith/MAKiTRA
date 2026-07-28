from personal_bot.core.entities.user import User
from personal_bot.core.enums import UserRole, UserStatus
from personal_bot.db.database import Database


class UserRepository:
    def __init__(self, database: Database) -> None:
        self._database = database

    def find_by_telegram_id(self, telegram_id: int) -> User | None:
        user_row = self._database.execute(
            """
            SELECT id, telegram_id, username, first_name, last_name, role, status
            FROM users
            WHERE telegram_id = ?
            """,
            (telegram_id,),
        ).fetchone()

        if user_row is None:
            return None

        return User(
            id=user_row["id"],
            telegram_id=user_row["telegram_id"],
            username=user_row["username"],
            first_name=user_row["first_name"],
            last_name=user_row["last_name"],
            role=UserRole(user_row["role"]),
            status=UserStatus(user_row["status"]),
        )

    def find_by_id(self, user_id: int) -> User | None:
        user_row = self._database.execute(
            """
            SELECT id, telegram_id, username, first_name, last_name, role, status
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        ).fetchone()

        if user_row is None:
            return None

        return User(
            id=user_row["id"],
            telegram_id=user_row["telegram_id"],
            username=user_row["username"],
            first_name=user_row["first_name"],
            last_name=user_row["last_name"],
            role=UserRole(user_row["role"]),
            status=UserStatus(user_row["status"]),
        )

    def has_any_users(self) -> bool:
        user_row = self._database.execute("SELECT 1 FROM users LIMIT 1").fetchone()
        return user_row is not None

    def create(
        self,
        telegram_id: int,
        username: str | None,
        first_name: str,
        last_name: str | None,
        phone_number: str,
        role: UserRole,
        status: UserStatus,
        created_at: str,
    ) -> int:
        cursor = self._database.execute(
            """
            INSERT INTO users (
                telegram_id,
                username,
                first_name,
                last_name,
                phone_number,
                role,
                status,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                telegram_id,
                username,
                first_name,
                last_name,
                phone_number,
                role.value,
                status.value,
                created_at,
                created_at,
            ),
        )
        return cursor.lastrowid

    def find_active_super_admins(self) -> list[User]:
        user_rows = self._database.execute(
            """
            SELECT id, telegram_id, username, first_name, last_name, role, status
            FROM users
            WHERE role = ? AND status = ?
            """,
            (UserRole.SUPER_ADMIN.value, UserStatus.ACTIVE.value),
        ).fetchall()

        return [
            User(
                id=user_row["id"],
                telegram_id=user_row["telegram_id"],
                username=user_row["username"],
                first_name=user_row["first_name"],
                last_name=user_row["last_name"],
                role=UserRole(user_row["role"]),
                status=UserStatus(user_row["status"]),
            )
            for user_row in user_rows
        ]
    
    def list_active_users(self) -> list[User]:
        user_rows = self._database.execute(
            """
            SELECT id, telegram_id, username, first_name, last_name, role, status
            FROM users
            WHERE status = ?
            ORDER BY first_name COLLATE NOCASE
            """,
            (UserStatus.ACTIVE.value,),
        ).fetchall()

        return [
            User(
                id=user_row["id"],
                telegram_id=user_row["telegram_id"],
                username=user_row["username"],
                first_name=user_row["first_name"],
                last_name=user_row["last_name"],
                role=UserRole(user_row["role"]),
                status=UserStatus(user_row["status"]),
            )
            for user_row in user_rows
        ]