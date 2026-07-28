import json

from personal_bot.core.entities.record import Record
from personal_bot.db.database import Database


class RecordRepository:
    def __init__(self, database: Database) -> None:
        self._database = database

    def create(
        self,
        owner_user_id: int,
        folder_id: int,
        type: str,
        name: str,
        payload: dict[str, object],
        sort_order: int,
        created_at: str,
        updated_at: str,
        preview_text: str | None = None,
    ) -> Record:
        cursor = self._database.execute(
            """
            INSERT INTO records (
                owner_user_id, folder_id, type, name, payload, sort_order,
                created_at, updated_at, preview_text
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                owner_user_id,
                folder_id,
                type,
                name,
                json.dumps(payload, ensure_ascii=False),
                sort_order,
                created_at,
                updated_at,
                preview_text,
            ),
        )
        return Record(
            id=cursor.lastrowid,
            owner_user_id=owner_user_id,
            folder_id=folder_id,
            type=type,
            name=name,
            payload=payload,
            sort_order=sort_order,
            created_at=created_at,
            updated_at=updated_at,
            preview_text=preview_text,
        )

    def get_by_id_and_owner(self, record_id: int, owner_user_id: int) -> Record | None:
        row = self._database.execute(
            """
            SELECT id, owner_user_id, folder_id, type, name, payload, sort_order,
                   created_at, updated_at, preview_text
            FROM records
            WHERE id = ? AND owner_user_id = ?
            """,
            (record_id, owner_user_id),
        ).fetchone()
        return self._row_to_record(row) if row is not None else None

    def get_by_id(self, record_id: int) -> Record | None:
        row = self._database.execute(
            """
            SELECT id, owner_user_id, folder_id, type, name, payload, sort_order,
                   created_at, updated_at, preview_text
            FROM records
            WHERE id = ?
            """,
            (record_id,),
        ).fetchone()
        return self._row_to_record(row) if row is not None else None

    def list_by_folder_and_owner(self, folder_id: int, owner_user_id: int) -> list[Record]:
        rows = self._database.execute(
            """
            SELECT id, owner_user_id, folder_id, type, name, payload, sort_order,
                   created_at, updated_at, preview_text
            FROM records
            WHERE folder_id = ? AND owner_user_id = ?
            ORDER BY sort_order ASC, id ASC
            """,
            (folder_id, owner_user_id),
        ).fetchall()
        return [self._row_to_record(row) for row in rows]

    def update(
        self,
        record_id: int,
        owner_user_id: int,
        name: str,
        payload: dict[str, object],
        updated_at: str,
        preview_text: str | None = None,
    ) -> Record | None:
        print("[DEBUG repository] SQL update record_id=", record_id)
        print("[DEBUG repository] SQL payload=", payload)
        cursor = self._database.execute(
            """
            UPDATE records
            SET name = ?, payload = ?, updated_at = ?, preview_text = ?
            WHERE id = ? AND owner_user_id = ?
            """,
            (
                name,
                json.dumps(payload, ensure_ascii=False),
                updated_at,
                preview_text,
                record_id,
                owner_user_id,
            ),
        )
        if cursor.rowcount == 0:
            return None
        return self.get_by_id_and_owner(record_id, owner_user_id)

    def delete(self, record_id: int, owner_user_id: int) -> bool:
        cursor = self._database.execute(
            "DELETE FROM records WHERE id = ? AND owner_user_id = ?",
            (record_id, owner_user_id),
        )
        return cursor.rowcount > 0

    def get_next_sort_order(self, folder_id: int, owner_user_id: int) -> int:
        row = self._database.execute(
            """
            SELECT COALESCE(MAX(sort_order), 0) AS max_sort_order
            FROM records
            WHERE folder_id = ? AND owner_user_id = ?
            """,
            (folder_id, owner_user_id),
        ).fetchone()
        return (row["max_sort_order"] or 0) + 1

    @staticmethod
    def _row_to_record(row) -> Record:
        return Record(
            id=row["id"],
            owner_user_id=row["owner_user_id"],
            folder_id=row["folder_id"],
            type=row["type"],
            name=row["name"],
            payload=json.loads(row["payload"]),
            sort_order=row["sort_order"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            preview_text=row["preview_text"],
        )
