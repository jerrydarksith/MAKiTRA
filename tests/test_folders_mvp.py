from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from types import SimpleNamespace

from personal_bot.core.enums import UserRole, UserStatus
from personal_bot.db.database import Database
from personal_bot.db.repositories.folder_repository import FolderRepository
from personal_bot.db.repositories.user_repository import UserRepository
from personal_bot.db.schema import initialize_database_schema
from personal_bot.folders.callback_handlers import FoldersMessageHandler
from personal_bot.folders.service import FoldersService


class FakeMessage:
    def __init__(self, text: str, user_id: int) -> None:
        self.text = text
        self.from_user = SimpleNamespace(id=user_id)
        self.replies: list[dict[str, object]] = []

    async def reply_text(self, text: str, reply_markup=None) -> None:
        self.replies.append({"text": text, "reply_markup": reply_markup})


class FakeUpdate:
    def __init__(self, message: FakeMessage) -> None:
        self.effective_message = message


class FakeUsersService:
    def find_user_by_telegram_id(self, telegram_id: int) -> SimpleNamespace | None:
        del telegram_id
        return SimpleNamespace(role=UserRole.SUPER_ADMIN)


class FoldersHandlerMVPTTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
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
        self.handler = FoldersMessageHandler(self.folders_service, FakeUsersService())

    async def asyncTearDown(self) -> None:
        self.database.close()
        self.temporary_directory.cleanup()

    def _make_update(self, text: str) -> FakeUpdate:
        return FakeUpdate(FakeMessage(text, user_id=1))

    async def test_open_folder_list_shows_reply_keyboard(self) -> None:
        update = self._make_update("📝 Записи")

        await self.handler.handle(update, None)

        message = update.effective_message
        self.assertEqual(len(message.replies), 1)
        self.assertIn("📝 Мої записи", message.replies[0]["text"])
        keyboard = message.replies[0]["reply_markup"]
        self.assertIsNotNone(keyboard)
        button_labels = [button.text for row in keyboard.keyboard for button in row]
        self.assertIn("➕ Створити папку", button_labels)
        self.assertIn("⬅ Назад", button_labels)

    async def test_create_folder_flow(self) -> None:
        create_update = self._make_update("➕ Створити папку")
        await self.handler.handle(create_update, None)

        name_update = self._make_update("Робота")
        await self.handler.handle(name_update, None)

        folder = self.folders_service.find_root_folder_by_name(owner_user_id=1, name="Робота")
        self.assertIsNotNone(folder)
        self.assertIn("📝 Мої записи", name_update.effective_message.replies[-1]["text"])

    async def test_open_folder_and_rename_flow(self) -> None:
        self.folders_service.create_folder(owner_user_id=1, name="Робота")

        list_update = self._make_update("📝 Записи")
        await self.handler.handle(list_update, None)

        folder_update = self._make_update("📁 Робота")
        await self.handler.handle(folder_update, None)

        rename_prompt_update = self._make_update("✏️ Перейменувати папку")
        await self.handler.handle(rename_prompt_update, None)

        renamed_update = self._make_update("Дом")
        await self.handler.handle(renamed_update, None)

        folder = self.folders_service.get_folder(folder_id=1, owner_user_id=1)
        self.assertIsNotNone(folder)
        self.assertEqual(folder.name, "Дом")
        self.assertIn("📁 Дом", renamed_update.effective_message.replies[-1]["text"])

    async def test_delete_confirmation_and_cancel_flow(self) -> None:
        self.folders_service.create_folder(owner_user_id=1, name="Робота")

        folder_update = self._make_update("📁 Робота")
        await self.handler.handle(folder_update, None)

        delete_update = self._make_update("🗑 Видалити папку")
        await self.handler.handle(delete_update, None)

        keyboard = delete_update.effective_message.replies[-1]["reply_markup"]
        button_labels = [button.text for row in keyboard.keyboard for button in row]
        self.assertIn("✅ Так", button_labels)
        self.assertIn("❌ Ні", button_labels)

        cancel_update = self._make_update("❌ Ні")
        await self.handler.handle(cancel_update, None)

        self.assertIn("📁 Робота", cancel_update.effective_message.replies[-1]["text"])

    async def test_back_from_folder_detail_returns_to_list(self) -> None:
        self.folders_service.create_folder(owner_user_id=1, name="Робота")

        folder_update = self._make_update("📁 Робота")
        await self.handler.handle(folder_update, None)

        back_update = self._make_update("⬅ Назад")
        await self.handler.handle(back_update, None)

        self.assertIn("📝 Мої записи", back_update.effective_message.replies[-1]["text"])
