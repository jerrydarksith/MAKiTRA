from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from personal_bot.core.enums import UserRole, UserStatus
from personal_bot.db.database import Database
from personal_bot.db.schema import initialize_database_schema


class DatabaseTransactionTests(unittest.TestCase):
    def test_transaction_rolls_back_changes_after_exception(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            database_path = Path(temporary_directory) / "personal_bot.sqlite3"
            database = Database(database_path)

            try:
                initialize_database_schema(database)

                with self.assertRaisesRegex(RuntimeError, "test failure"):
                    with database.transaction():
                        database.execute(
                            """
                            INSERT INTO users (
                                telegram_id,
                                first_name,
                                phone_number,
                                role,
                                status,
                                created_at,
                                updated_at
                            )
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                123456,
                                "Ім'я",
                                "+380000000000",
                                UserRole.USER.value,
                                UserStatus.ACTIVE.value,
                                "now",
                                "now",
                            ),
                        )
                        raise RuntimeError("test failure")

                user_row = database.execute("SELECT COUNT(*) AS count FROM users").fetchone()
            finally:
                database.close()

        self.assertEqual(user_row["count"], 0)


if __name__ == "__main__":
    unittest.main()
