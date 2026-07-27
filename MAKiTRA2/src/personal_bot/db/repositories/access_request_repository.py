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
    ) -> AccessRequest:
        cursor = self._database.execute(
            """
            INSERT INTO access_requests (
                telegram_id,
                username,
                first_name,
                last_name,
                phone_number,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                telegram_id,
                username,
                first_name,
                last_name,
                phone_number,
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
            SELECT id, telegram_id, username, first_name, last_name, phone_number,
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
