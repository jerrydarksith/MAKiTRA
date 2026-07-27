from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from personal_bot.core.enums import UserRole, UserStatus
from personal_bot.db.database import Database
from personal_bot.db.repositories.folder_repository import FolderRepository
from personal_bot.db.repositories.record_repository import RecordRepository
from personal_bot.db.repositories.user_repository import UserRepository
from personal_bot.db.schema import initialize_database_schema
from personal_bot.records.registry import RecordRegistry, create_record_registry


class RecordTypeStub:
    def create_initial_data(self) -> dict[str, object]:
        return {}

    def validate(self, payload: dict[str, object]) -> None:
        return None

    def serialize(self, data: dict[str, object]) -> dict[str, object]:
        return data

    def deserialize(self, payload: dict[str, object]) -> dict[str, object]:
        return payload

    def render(self, payload: dict[str, object]) -> str:
        return ""

    def preview(self, payload: dict[str, object]) -> str:
        return ""

    def build_editor_steps(self) -> tuple[object, ...]:
        return ()


class RecordInfrastructureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = TemporaryDirectory()
        self.database_path = Path(self.temporary_directory.name) / "personal_bot.sqlite3"
        self.database = Database(self.database_path)
        initialize_database_schema(self.database)

        self.user_repository = UserRepository(self.database)
        self.user_repository.create(
            telegram_id=1,
            username="owner",
            first_name="Owner",
            last_name=None,
            phone_number="+380000000001",
            role=UserRole.SUPER_ADMIN,
            status=UserStatus.ACTIVE,
            created_at="2026-01-01T00:00:00+00:00",
        )
        self.folder_repository = FolderRepository(self.database)
        self.folder = self.folder_repository.create(
            owner_user_id=1,
            parent_id=None,
            name="Робота",
            sort_order=1,
            created_at="2026-01-01T00:00:00+00:00",
            updated_at="2026-01-01T00:00:00+00:00",
        )
        self.record_repository = RecordRepository(self.database)

    def tearDown(self) -> None:
        self.database.close()
        self.temporary_directory.cleanup()

    def test_repository_creates_and_reads_record(self) -> None:
        record = self.record_repository.create(
            owner_user_id=1,
            folder_id=self.folder.id,
            type="short_text",
            name="Назва",
            payload={"value": "Привіт"},
            sort_order=1,
            created_at="2026-01-01T00:00:00+00:00",
            updated_at="2026-01-01T00:00:00+00:00",
            preview_text="Привіт",
        )

        fetched = self.record_repository.get_by_id_and_owner(record.id, owner_user_id=1)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.name, "Назва")
        self.assertEqual(fetched.payload, {"value": "Привіт"})

    def test_repository_lists_records_only_for_folder_and_owner(self) -> None:
        self.record_repository.create(
            owner_user_id=1,
            folder_id=self.folder.id,
            type="short_text",
            name="Перший",
            payload={"value": "Один"},
            sort_order=1,
            created_at="2026-01-01T00:00:00+00:00",
            updated_at="2026-01-01T00:00:00+00:00",
            preview_text="Один",
        )
        self.record_repository.create(
            owner_user_id=1,
            folder_id=self.folder.id,
            type="short_text",
            name="Другий",
            payload={"value": "Два"},
            sort_order=2,
            created_at="2026-01-01T00:00:00+00:00",
            updated_at="2026-01-01T00:00:00+00:00",
            preview_text="Два",
        )

        records = self.record_repository.list_by_folder_and_owner(folder_id=self.folder.id, owner_user_id=1)
        self.assertEqual(len(records), 2)

        foreign_record = self.record_repository.get_by_id_and_owner(
            records[0].id,
            owner_user_id=2,
        )
        self.assertIsNone(foreign_record)

    def test_repository_updates_deletes_and_calculates_next_sort_order(self) -> None:
        record = self.record_repository.create(
            owner_user_id=1,
            folder_id=self.folder.id,
            type="short_text",
            name="Чернетка",
            payload={"value": "До"},
            sort_order=1,
            created_at="2026-01-01T00:00:00+00:00",
            updated_at="2026-01-01T00:00:00+00:00",
        )

        updated = self.record_repository.update(
            record_id=record.id,
            owner_user_id=1,
            name="Готово",
            payload={"value": "Після"},
            updated_at="2026-01-02T00:00:00+00:00",
            preview_text="Після",
        )

        self.assertIsNotNone(updated)
        self.assertEqual(updated.name, "Готово")
        self.assertEqual(updated.payload, {"value": "Після"})
        self.assertEqual(updated.preview_text, "Після")
        self.assertEqual(
            self.record_repository.get_next_sort_order(self.folder.id, owner_user_id=1),
            2,
        )
        self.assertTrue(self.record_repository.delete(record.id, owner_user_id=1))
        self.assertIsNone(
            self.record_repository.get_by_id_and_owner(record.id, owner_user_id=1)
        )

    def test_registry_is_created_without_record_types(self) -> None:
        registry = create_record_registry()
        self.assertIsInstance(registry, RecordRegistry)
        self.assertEqual(registry.list_available_types(), ())
        self.assertIsNone(registry.get("short_text"))

    def test_registry_registers_and_returns_record_type(self) -> None:
        registry = RecordRegistry()
        record_type = RecordTypeStub()

        registry.register("test", record_type)

        self.assertEqual(registry.list_available_types(), ("test",))
        self.assertIs(registry.get("test"), record_type)


if __name__ == "__main__":
    unittest.main()
