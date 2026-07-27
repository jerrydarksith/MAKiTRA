from personal_bot.core.entities.folder import Folder
from personal_bot.db.database import Database


class FolderRepository:
    def __init__(self, database: Database) -> None:
        self._database = database

    def create(
        self,
        owner_user_id: int,
        parent_id: int | None,
        name: str,
        sort_order: int,
        created_at: str,
        updated_at: str,
    ) -> Folder:
        cursor = self._database.execute(
            """
            INSERT INTO folders (
                owner_user_id,
                parent_id,
                name,
                sort_order,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (owner_user_id, parent_id, name, sort_order, created_at, updated_at),
        )

        return Folder(
            id=cursor.lastrowid,
            owner_user_id=owner_user_id,
            parent_id=parent_id,
            name=name,
            sort_order=sort_order,
        )

    def list_root_folders(self, owner_user_id: int) -> list[Folder]:
        rows = self._database.execute(
            """
            SELECT id, owner_user_id, parent_id, name, sort_order
            FROM folders
            WHERE owner_user_id = ? AND parent_id IS NULL
            ORDER BY sort_order ASC, name COLLATE NOCASE
            """,
            (owner_user_id,),
        ).fetchall()

        return [
            Folder(
                id=row["id"],
                owner_user_id=row["owner_user_id"],
                parent_id=row["parent_id"],
                name=row["name"],
                sort_order=row["sort_order"],
            )
            for row in rows
        ]

    def find_root_folder_by_name(self, owner_user_id: int, name: str) -> Folder | None:
        row = self._database.execute(
            """
            SELECT id, owner_user_id, parent_id, name, sort_order
            FROM folders
            WHERE owner_user_id = ? AND parent_id IS NULL AND name = ?
            LIMIT 1
            """,
            (owner_user_id, name),
        ).fetchone()

        if row is None:
            return None

        return Folder(
            id=row["id"],
            owner_user_id=row["owner_user_id"],
            parent_id=row["parent_id"],
            name=row["name"],
            sort_order=row["sort_order"],
        )

    def find_by_id_and_owner(self, folder_id: int, owner_user_id: int) -> Folder | None:
        row = self._database.execute(
            """
            SELECT id, owner_user_id, parent_id, name, sort_order
            FROM folders
            WHERE id = ? AND owner_user_id = ?
            LIMIT 1
            """,
            (folder_id, owner_user_id),
        ).fetchone()

        if row is None:
            return None

        return Folder(
            id=row["id"],
            owner_user_id=row["owner_user_id"],
            parent_id=row["parent_id"],
            name=row["name"],
            sort_order=row["sort_order"],
        )

    def update_name(
        self,
        folder_id: int,
        owner_user_id: int,
        name: str,
        updated_at: str,
    ) -> Folder | None:
        cursor = self._database.execute(
            """
            UPDATE folders
            SET name = ?, updated_at = ?
            WHERE id = ? AND owner_user_id = ?
            """,
            (name, updated_at, folder_id, owner_user_id),
        )

        if cursor.rowcount == 0:
            return None

        return self.find_by_id_and_owner(folder_id, owner_user_id)

    def delete(self, folder_id: int, owner_user_id: int) -> bool:
        cursor = self._database.execute(
            """
            DELETE FROM folders
            WHERE id = ? AND owner_user_id = ?
            """,
            (folder_id, owner_user_id),
        )

        return cursor.rowcount > 0

    def is_empty(self, folder_id: int, owner_user_id: int) -> bool:
        child_row = self._database.execute(
            """
            SELECT 1 FROM folders
            WHERE parent_id = ? AND owner_user_id = ?
            LIMIT 1
            """,
            (folder_id, owner_user_id),
        ).fetchone()

        return child_row is None

    def get_next_sort_order(self, owner_user_id: int) -> int:
        row = self._database.execute(
            """
            SELECT COALESCE(MAX(sort_order), 0) AS max_sort_order
            FROM folders
            WHERE owner_user_id = ?
            """,
            (owner_user_id,),
        ).fetchone()

        return (row["max_sort_order"] or 0) + 1
