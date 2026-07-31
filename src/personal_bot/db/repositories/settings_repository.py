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

    def get_registration_mode(self) -> str:
        value = self._get_global_setting("registration_mode")
        if value is None:
            self.set_registration_mode("manual")
            return "manual"
        return value

    def set_registration_mode(self, registration_mode: str) -> None:
        self._set_global_setting("registration_mode", registration_mode)

    def get_notify_new_users(self) -> bool:
        value = self._get_global_setting("notify_new_users")
        if value is None:
            self.set_notify_new_users(True)
            return True
        return value == "1"

    def set_notify_new_users(self, enabled: bool) -> None:
        self._set_global_setting("notify_new_users", "1" if enabled else "0")

    def _get_global_setting(self, key: str) -> str | None:
        row = self._database.execute(
            "SELECT value FROM bot_settings WHERE key = ?",
            (key,),
        ).fetchone()
        return None if row is None else row["value"]

    def _set_global_setting(self, key: str, value: str) -> None:
        self._database.execute(
            """
            INSERT INTO bot_settings (key, value)
            VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (key, value),
        )
