from __future__ import annotations

from personal_bot.db.database import Database


class ReminderRepository:
    def __init__(self, database: Database) -> None:
        self._database = database
        self._has_owner_user_id = any(
            row["name"] == "owner_user_id"
            for row in self._database.execute("PRAGMA table_info(reminders)").fetchall()
        )

    def create(
        self,
        *,
        owner_user_id: int | None,
        record_id: int,
        text: str,
        remind_at: str,
        status: str,
        created_at: str,
    ) -> dict[str, object]:
        if self._has_owner_user_id:
            resolved_owner_user_id = owner_user_id
            if resolved_owner_user_id is None:
                resolved_owner_user_id = self._resolve_record_owner_user_id(record_id)
            cursor = self._database.execute(
                """
                INSERT INTO reminders (
                    owner_user_id, record_id, text, remind_at, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (resolved_owner_user_id, record_id, text, remind_at, status, created_at),
            )
            reminder_data = {
                "id": cursor.lastrowid,
                "owner_user_id": resolved_owner_user_id,
                "record_id": record_id,
                "text": text,
                "remind_at": remind_at,
                "status": status,
                "created_at": created_at,
            }
        else:
            cursor = self._database.execute(
                """
                INSERT INTO reminders (
                    record_id, text, remind_at, status, created_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (record_id, text, remind_at, status, created_at),
            )
            reminder_data = {
                "id": cursor.lastrowid,
                "owner_user_id": None,
                "record_id": record_id,
                "text": text,
                "remind_at": remind_at,
                "status": status,
                "created_at": created_at,
            }
        return reminder_data

    def list_active_due(self, now: str) -> list[dict[str, object]]:
        rows = self._database.execute(
            """
            SELECT r.id, rec.owner_user_id, r.record_id, r.text, r.remind_at, r.status, r.created_at
            FROM reminders AS r
            JOIN records AS rec ON rec.id = r.record_id
            WHERE r.status = 'active' AND r.remind_at <= ?
            ORDER BY r.remind_at ASC
            """,
            (now,),
        ).fetchall()
        return [
            {
                "id": row["id"],
                "owner_user_id": row["owner_user_id"],
                "record_id": row["record_id"],
                "text": row["text"],
                "remind_at": row["remind_at"],
                "status": row["status"],
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    def mark_sent(self, reminder_id: int) -> None:
        self._database.execute(
            "UPDATE reminders SET status = 'sent' WHERE id = ?",
            (reminder_id,),
        )

    def _resolve_record_owner_user_id(self, record_id: int) -> int | None:
        row = self._database.execute(
            "SELECT owner_user_id FROM records WHERE id = ?",
            (record_id,),
        ).fetchone()
        if row is None:
            return None
        return row["owner_user_id"]
