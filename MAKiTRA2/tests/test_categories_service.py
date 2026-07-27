from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from personal_bot.core.entities.category import Category
from personal_bot.core.enums import UserRole, UserStatus
from personal_bot.db.database import Database
from personal_bot.db.repositories.category_repository import CategoryRepository
from personal_bot.db.repositories.user_repository import UserRepository
from personal_bot.db.schema import initialize_database_schema
from personal_bot.categories.service import CategoriesService


class CategoriesServiceTests(unittest.TestCase):
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
        self.category_repository = CategoryRepository(self.database)
        self.categories_service = CategoriesService(self.category_repository)

    def tearDown(self) -> None:
        self.database.close()
        self.temporary_directory.cleanup()

    def test_create_category_and_build_tree(self) -> None:
        root_category = self.categories_service.create_category(
            owner_user_id=1,
            name="Root",
            icon="📁",
        )
        child_category = self.categories_service.create_category(
            owner_user_id=1,
            name="Child",
            parent_id=root_category.id,
            icon="📄",
        )

        tree = self.categories_service.build_tree_message(owner_user_id=1)

        self.assertIsInstance(root_category, Category)
        self.assertIsInstance(child_category, Category)
        self.assertIn("Root", tree)
        self.assertIn("Child", tree)
        self.assertIn("📁", tree)
        self.assertIn("📄", tree)


if __name__ == "__main__":
    unittest.main()
