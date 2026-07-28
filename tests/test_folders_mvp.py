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
        # Return a User-like object where internal id is different from telegram id
        # This simulates a real User object with separate fields.
        return SimpleNamespace(id=1, telegram_id=999, role=UserRole.SUPER_ADMIN)


class FakeRecordsService:
    def __init__(self) -> None:
        self.created_records: list[dict[str, object]] = []

    def create_record(self, **kwargs) -> SimpleNamespace:
        record = dict(kwargs)
        record["id"] = len(self.created_records) + 1
        self.created_records.append(record)
        record_args = dict(record)
        record_args.pop("id", None)
        payload = record_args.get("data", {})
        record_args["payload"] = payload
        return SimpleNamespace(id=record["id"], **record_args)

    def get_record(self, record_id: int, owner_user_id: int) -> SimpleNamespace | None:
        for record in self.created_records:
            if record["id"] == record_id and record["owner_user_id"] == owner_user_id:
                record_args = dict(record)
                record_args.pop("id", None)
                record_args["payload"] = record_args.get("data", {})
                return SimpleNamespace(id=record["id"], **record_args)
        return None

    def update_record(self, record_id: int, owner_user_id: int, data: dict[str, object]) -> SimpleNamespace:
        for record in self.created_records:
            if record["id"] == record_id and record["owner_user_id"] == owner_user_id:
                payload_data = dict(data)
                new_name = payload_data.pop("name", record.get("name"))
                if isinstance(new_name, str):
                    record["name"] = new_name
                record["data"] = payload_data
                record_args = dict(record)
                record_args.pop("id", None)
                record_args["payload"] = payload_data
                return SimpleNamespace(id=record["id"], **record_args)
        raise ValueError("record not found")

    def list_records(self, folder_id: int, owner_user_id: int) -> list[SimpleNamespace]:
        return [
            SimpleNamespace(id=record["id"], name=record["name"])
            for record in self.created_records
            if record["folder_id"] == folder_id
            and record["owner_user_id"] == owner_user_id
        ]


class FakeRecordRegistry:
    def list_available_types(self) -> tuple[str, ...]:
        return ("short_text",)


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
        self.folders_service = FoldersService(self.database, self.folder_repository)
        self.records_service = FakeRecordsService()
        self.handler = FoldersMessageHandler(
            self.folders_service,
            FakeUsersService(),
            self.records_service,
            FakeRecordRegistry(),
        )

    async def asyncTearDown(self) -> None:
        self.database.close()
        self.temporary_directory.cleanup()

    def _make_update(self, text: str) -> FakeUpdate:
        return FakeUpdate(FakeMessage(text, user_id=1))

    async def test_open_folder_list_shows_reply_keyboard(self) -> None:
        update = self._make_update("📝 Записи")

        await self.handler.handle(update, None)

        message = update.effective_message
        self.assertGreaterEqual(len(message.replies), 1)
        self.assertEqual("📂 Мої записи", message.replies[0]["text"])
        keyboard = message.replies[0]["reply_markup"]
        self.assertIsNotNone(keyboard)
        button_labels = [button.text for row in keyboard.keyboard for button in row]
        self.assertIn("📁 Створити папку", button_labels)
        self.assertIn("⬅️ Назад", button_labels)

    async def test_child_folder_navigation_uses_path_message(self) -> None:
        self.folders_service.create_folder(owner_user_id=1, name="Робота")

        await self.handler.handle(self._make_update("📝 Записи"), None)
        await self.handler.handle(self._make_update("📁 Робота"), None)

        message = self._make_update("📁 Робота")
        await self.handler.handle(message, None)

        self.assertEqual(message.effective_message.replies[-1]["text"], "📂 Мої записи / Робота")

    async def test_create_folder_flow(self) -> None:
        create_update = self._make_update("➕ Створити папку")
        await self.handler.handle(create_update, None)

        name_update = self._make_update("Робота")
        await self.handler.handle(name_update, None)

        folder = self.folders_service.find_root_folder_by_name(owner_user_id=1, name="Робота")
        self.assertIsNotNone(folder)
        self.assertIn("� Мої записи", name_update.effective_message.replies[-1]["text"])

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
        self.assertIn("� Мої записи / Дом", renamed_update.effective_message.replies[-1]["text"])

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

        self.assertIn("� Мої записи / Робота", cancel_update.effective_message.replies[-1]["text"])

    async def test_back_from_folder_detail_returns_to_list(self) -> None:
        self.folders_service.create_folder(owner_user_id=1, name="Робота")

        folder_update = self._make_update("📁 Робота")
        await self.handler.handle(folder_update, None)

        back_update = self._make_update("⬅ Назад")
        await self.handler.handle(back_update, None)

        self.assertIn("� Мої записи", back_update.effective_message.replies[-1]["text"])

    async def test_create_record_flow_opens_record_page_and_field_menu(self) -> None:
        self.handler._start_folder_session(1, 1, page=0)

        new_record_update = self._make_update("➕ Новий запис")
        await self.handler.handle(new_record_update, None)

        self.assertEqual(new_record_update.effective_message.replies[-1]["text"], "Введіть назву запису.")

        create_record_update = self._make_update("Заміна масла")
        await self.handler.handle(create_record_update, None)

        self.assertEqual(len(self.records_service.created_records), 1)
        self.assertEqual(
            self.records_service.created_records[0]["name"],
            "Заміна масла",
        )
        self.assertEqual(self.records_service.created_records[0]["type_code"], "short_text")
        self.assertIn("📄 Заміна масла", create_record_update.effective_message.replies[-1]["text"])
        self.assertIn("Поки що дані відсутні.", create_record_update.effective_message.replies[-1]["text"])

        keyboard = create_record_update.effective_message.replies[-1]["reply_markup"]
        button_labels = [button.text for row in keyboard.keyboard for button in row]
        self.assertIn("➕ Додати дані", button_labels)
        self.assertIn("⚙️ Дії", button_labels)
        self.assertIn("⬅️ До папки", button_labels)

        add_data_update = self._make_update("➕ Додати дані")
        await self.handler.handle(add_data_update, None)

        field_keyboard = add_data_update.effective_message.replies[-1]["reply_markup"]
        field_button_labels = [button.text for row in field_keyboard.keyboard for button in row]
        self.assertIn("📝 Текст", field_button_labels)
        self.assertIn("📄 Великий текст", field_button_labels)
        self.assertIn("⬅️ Назад", field_button_labels)

    async def test_add_data_flow_for_default_named_field_skips_name_prompt(self) -> None:
        self.handler._start_folder_session(1, 1, page=0)

        await self.handler.handle(self._make_update("➕ Новий запис"), None)
        await self.handler.handle(self._make_update("Заміна масла"), None)
        await self.handler.handle(self._make_update("➕ Додати дані"), None)
        await self.handler.handle(self._make_update("💰 Сума"), None)

        self.assertEqual(self.handler._pending_action_for_user[1], "enter_field_value")
        self.assertEqual(self.handler._pending_field_data_for_user[1]["name"], "Сума")
        self.assertEqual(self.handler._pending_field_data_for_user[1]["type"], "money")

        await self.handler.handle(self._make_update("1500"), None)

        record = self.records_service.created_records[0]
        self.assertIn("fields", record["data"])
        self.assertEqual(record["data"]["fields"][0]["name"], "Сума")
        self.assertEqual(record["data"]["fields"][0]["value"], "1500")
        self.assertEqual(record["data"]["fields"][0]["type"], "money")

    async def test_open_existing_record_from_folder_list_opens_that_record_page(self) -> None:
        self.handler._start_folder_session(1, 1, page=0)

        await self.handler.handle(self._make_update("➕ Новий запис"), None)
        await self.handler.handle(self._make_update("Заміна масла"), None)
        await self.handler.handle(self._make_update("📝 Заміна масла"), None)

        message = self.handler._selected_record_id_for_user[1]
        self.assertEqual(message, 1)

    async def test_rename_record_updates_name_and_reopens_record(self) -> None:
        self.handler._start_folder_session(1, 1, page=0)

        await self.handler.handle(self._make_update("➕ Новий запис"), None)
        await self.handler.handle(self._make_update("Заміна масла"), None)
        await self.handler.handle(self._make_update("⚙️ Дії із записом"), None)
        await self.handler.handle(self._make_update("✏️ Перейменувати запис"), None)
        await self.handler.handle(self._make_update("Заміна двигуна"), None)

        record = self.records_service.created_records[0]
        self.assertEqual(record["name"], "Заміна двигуна")
        self.assertEqual(record["data"]["value"], "Заміна масла")

    async def test_edit_existing_field_value_updates_only_that_field(self) -> None:
        self.handler._start_folder_session(1, 1, page=0)

        await self.handler.handle(self._make_update("➕ Новий запис"), None)
        await self.handler.handle(self._make_update("Заміна масла"), None)
        await self.handler.handle(self._make_update("➕ Додати дані"), None)
        await self.handler.handle(self._make_update("📝 Текст"), None)
        await self.handler.handle(self._make_update("Сума"), None)
        await self.handler.handle(self._make_update("1500"), None)
        await self.handler.handle(self._make_update("⚙️ Дії із записом"), None)
        await self.handler.handle(self._make_update("📝 Редагувати поля"), None)
        await self.handler.handle(self._make_update("Сума"), None)
        await self.handler.handle(self._make_update("✏️ Змінити значення"), None)
        await self.handler.handle(self._make_update("1800"), None)

        record = self.records_service.created_records[0]
        self.assertEqual(record["data"]["fields"][0]["name"], "Сума")
        self.assertEqual(record["data"]["fields"][0]["value"], "1800")
        self.assertEqual(record["data"]["fields"][0]["type"], "text")

    async def test_edit_field_value_reprompts_when_value_is_empty(self) -> None:
        self.handler._start_folder_session(1, 1, page=0)

        await self.handler.handle(self._make_update("➕ Новий запис"), None)
        await self.handler.handle(self._make_update("Заміна масла"), None)
        await self.handler.handle(self._make_update("➕ Додати дані"), None)
        await self.handler.handle(self._make_update("📝 Текст"), None)
        await self.handler.handle(self._make_update("Сума"), None)
        await self.handler.handle(self._make_update("1500"), None)
        await self.handler.handle(self._make_update("⚙️ Дії із записом"), None)
        await self.handler.handle(self._make_update("📝 Редагувати поля"), None)
        await self.handler.handle(self._make_update("Сума"), None)
        await self.handler.handle(self._make_update("✏️ Змінити значення"), None)
        empty_update = self._make_update("   ")
        await self.handler.handle(empty_update, None)

        self.assertEqual(self.handler._pending_action_for_user[1], "edit_field_value")
        self.assertEqual(empty_update.effective_message.replies[-1]["text"], "Значення не може бути порожнім.")
        self.assertEqual(
            self.handler._pending_field_data_for_user[1]["record_id"],
            1,
        )

    async def test_record_actions_menu_opens_for_record_page(self) -> None:
        self.handler._start_folder_session(1, 1, page=0)

        await self.handler.handle(self._make_update("➕ Новий запис"), None)
        await self.handler.handle(self._make_update("Заміна масла"), None)
        await self.handler.handle(self._make_update("⚙️ Дії із записом"), None)

        self.assertEqual(self.handler._record_actions_for_user[1], "record_actions")

    async def test_edit_fields_menu_lists_existing_fields(self) -> None:
        self.handler._start_folder_session(1, 1, page=0)

        await self.handler.handle(self._make_update("➕ Новий запис"), None)
        await self.handler.handle(self._make_update("Заміна масла"), None)
        await self.handler.handle(self._make_update("➕ Додати дані"), None)
        await self.handler.handle(self._make_update("📝 Текст"), None)
        await self.handler.handle(self._make_update("Коментар"), None)
        await self.handler.handle(self._make_update("Тест"), None)
        await self.handler.handle(self._make_update("⚙️ Дії із записом"), None)
        await self.handler.handle(self._make_update("📝 Редагувати поля"), None)

        last_reply = self.handler._selected_record_id_for_user[1]
        self.assertEqual(last_reply, 1)

        field_list_reply = self.handler._record_actions_for_user[1]
        self.assertEqual(field_list_reply, "record_fields_list")

    async def test_add_data_flow_saves_field_and_returns_to_record_page(self) -> None:
        self.handler._start_folder_session(1, 1, page=0)

        await self.handler.handle(self._make_update("➕ Новий запис"), None)
        await self.handler.handle(self._make_update("Заміна масла"), None)
        await self.handler.handle(self._make_update("➕ Додати дані"), None)
        await self.handler.handle(self._make_update("📝 Текст"), None)
        await self.handler.handle(self._make_update("Дата заміни"), None)
        await self.handler.handle(self._make_update("28.07.2026"), None)

        record = self.records_service.created_records[0]
        self.assertIn("fields", record["data"])
        self.assertEqual(record["data"]["fields"][0]["name"], "Дата заміни")
        self.assertEqual(record["data"]["fields"][0]["value"], "28.07.2026")
        self.assertEqual(record["data"]["fields"][0]["type"], "text")
