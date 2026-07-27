from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from personal_bot.bootstrap import run_application
from personal_bot.config import ApplicationSettings
from personal_bot.records.registry import RecordRegistry
from personal_bot.records.types.short_text import ShortTextRecordType


class FakeTelegramApplication:
    def __init__(self) -> None:
        self.run_polling_calls = 0

    def run_polling(self) -> None:
        self.run_polling_calls += 1


class RecordsBootstrapTests(unittest.TestCase):
    def test_bootstrap_registers_short_text_in_production_registry(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            registry = RecordRegistry()
            application = FakeTelegramApplication()
            settings = ApplicationSettings(
                database_path=Path(temporary_directory) / "personal_bot.sqlite3",
                telegram_bot_token="test-token",
            )

            with (
                patch(
                    "personal_bot.bootstrap.load_application_settings",
                    return_value=settings,
                ),
                patch(
                    "personal_bot.bootstrap.create_record_registry",
                    return_value=registry,
                ),
                patch(
                    "personal_bot.bootstrap.create_telegram_application",
                    return_value=application,
                ),
            ):
                run_application()

        record_type = registry.get("short_text")
        self.assertIsInstance(record_type, ShortTextRecordType)
        self.assertIn("short_text", registry.list_available_types())
        self.assertEqual(application.run_polling_calls, 1)


if __name__ == "__main__":
    unittest.main()
