from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from personal_bot.core.entities.folder import Folder
from personal_bot.core.enums import UserRole, UserStatus
from personal_bot.db.database import Database
from personal_bot.db.repositories.folder_repository import FolderRepository
from personal_bot.db.repositories.user_repository import UserRepository
from personal_bot.db.schema import initialize_database_schema
from personal_bot.folders.service import FoldersService


class FoldersServiceTests(unittest.TestCase):
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
        self.folders_service = FoldersService(self.folder_repository)

    def tearDown(self) -> None:
        self.database.close()
        self.temporary_directory.cleanup()

    def test_build_folder_list_message_on_empty_collection(self) -> None:
        message = self.folders_service.build_folder_list_message(owner_user_id=1)

        self.assertIn("📝 Мої записи", message)
        self.assertIn("немає жодної папки", message)

    def test_create_folder_and_find_folder(self) -> None:
        folder = self.folders_service.create_folder(owner_user_id=1, name="Робота")
        self.assertIsInstance(folder, Folder)
        self.assertEqual(folder.name, "Робота")

        found_folder = self.folders_service.find_root_folder_by_name(owner_user_id=1, name="Робота")
        self.assertIsNotNone(found_folder)
        self.assertEqual(found_folder.name, "Робота")

    def test_update_folder_name(self) -> None:
        folder = self.folders_service.create_folder(owner_user_id=1, name="Робота")
        updated = self.folders_service.update_folder_name(
            folder_id=folder.id,
            owner_user_id=1,
            name="Дом",
        )

        self.assertIsNotNone(updated)
        self.assertEqual(updated.name, "Дом")

    def test_delete_folder_when_empty(self) -> None:
        folder = self.folders_service.create_folder(owner_user_id=1, name="Робота")
        self.assertTrue(self.folders_service.can_delete_folder(folder.id, owner_user_id=1))
        self.assertTrue(self.folders_service.delete_folder(folder.id, owner_user_id=1))

    def test_build_folder_page_message(self) -> None:
        folder = self.folders_service.create_folder(owner_user_id=1, name="Робота")
        page = self.folders_service.build_folder_page_message(folder)
        self.assertIn("📁 Робота", page)
        self.assertIn("Папка порожня", page)


if __name__ == "__main__":
    unittest.main()
