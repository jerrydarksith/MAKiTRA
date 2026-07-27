from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from personal_bot.db.database import Database
from personal_bot.db.schema import initialize_database_schema


class DatabaseSchemaTests(unittest.TestCase):
    def test_initialize_database_schema_creates_first_stage_tables(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            database_path = Path(temporary_directory) / "personal_bot.sqlite3"
            database = Database(database_path)

            try:
                initialize_database_schema(database)
                table_rows = database.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                ).fetchall()
            finally:
                database.close()

        table_names = {table_row["name"] for table_row in table_rows}
        self.assertTrue(
            {"users", "access_requests", "user_settings", "categories", "folders"}
            .issubset(table_names)
        )


if __name__ == "__main__":
    unittest.main()
