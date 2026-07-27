from personal_bot.db.database import Database


class SettingsRepository:
    def __init__(self, database: Database) -> None:
        self._database = database

    def create_default(self, user_id: int, created_at: str) -> None:
        self._database.execute(
            """
            INSERT INTO user_settings (
                user_id,
                timezone,
                currency,
                date_format,
                language,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, "Europe/Kyiv", "UAH", "DD.MM.YYYY", "uk", created_at),
        )
