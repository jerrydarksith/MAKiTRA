from personal_bot.core.entities.category import Category
from personal_bot.db.database import Database


class CategoryRepository:
    def __init__(self, database: Database) -> None:
        self._database = database

    def create(
        self,
        owner_user_id: int,
        parent_id: int | None,
        name: str,
        icon: str,
        created_at: str,
        updated_at: str,
    ) -> Category:
        cursor = self._database.execute(
            """
            INSERT INTO categories (
                owner_user_id,
                parent_id,
                name,
                icon,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (owner_user_id, parent_id, name, icon, created_at, updated_at),
        )
        return Category(
            id=cursor.lastrowid,
            owner_user_id=owner_user_id,
            parent_id=parent_id,
            name=name,
            icon=icon,
        )

    def list_by_owner(self, owner_user_id: int) -> list[Category]:
        rows = self._database.execute(
            """
            SELECT id, owner_user_id, parent_id, name, icon
            FROM categories
            WHERE owner_user_id = ?
            ORDER BY parent_id IS NULL DESC, parent_id, name COLLATE NOCASE
            """,
            (owner_user_id,),
        ).fetchall()

        return [
            Category(
                id=row["id"],
                owner_user_id=row["owner_user_id"],
                parent_id=row["parent_id"],
                name=row["name"],
                icon=row["icon"],
            )
            for row in rows
        ]
