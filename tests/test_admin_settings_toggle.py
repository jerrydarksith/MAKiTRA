from pathlib import Path
import re
from tempfile import TemporaryDirectory
import unittest
from types import SimpleNamespace

from personal_bot.access.service import AccessService
from personal_bot.core.entities.user import User
from personal_bot.core.enums import UserRole, UserStatus
from personal_bot.db.database import Database
from personal_bot.db.repositories.access_request_repository import AccessRequestRepository
from personal_bot.db.repositories.settings_repository import SettingsRepository
from personal_bot.db.repositories.user_repository import UserRepository
from personal_bot.db.schema import initialize_database_schema
from personal_bot.telegram.application import get_admin_settings_menu_regex
from personal_bot.users.callback_handlers import UsersMessageHandler
from personal_bot.users.service import UsersService


class DummyMessage:
    def __init__(self, text: str) -> None:
        self.text = text
        self.replies: list[tuple[str, object | None]] = []
        self.from_user = SimpleNamespace(id=1)

    async def reply_text(self, text: str, reply_markup=None) -> None:
        self.replies.append((text, reply_markup))


class DummyContext:
    def __init__(self) -> None:
        self.user_data = {}


class AdminSettingsToggleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = TemporaryDirectory()
        self.database_path = Path(self.temporary_directory.name) / "personal_bot.sqlite3"
        self.database = Database(self.database_path)
        initialize_database_schema(self.database)

        self.user_repository = UserRepository(self.database)
        self.settings_repository = SettingsRepository(self.database)
        self.access_request_repository = AccessRequestRepository(self.database)
        self.users_service = UsersService(self.user_repository)
        self.access_service = AccessService(
            database=self.database,
            user_repository=self.user_repository,
            settings_repository=self.settings_repository,
            access_request_repository=self.access_request_repository,
        )
        self.handler = UsersMessageHandler(self.users_service, self.access_service)
        self.user_repository.create(
            telegram_id=1,
            username="admin",
            first_name="Адмін",
            last_name=None,
            phone_number=None,
            role=UserRole.SUPER_ADMIN,
            status=UserStatus.ACTIVE,
            created_at="2026-01-01T00:00:00+00:00",
        )

    def tearDown(self) -> None:
        self.database.close()
        self.temporary_directory.cleanup()

    def test_registration_toggle_responds_to_stateful_button_label(self) -> None:
        message = DummyMessage("🔴 Реєстрація: Через підтвердження")
        update = SimpleNamespace(effective_message=message)

        import asyncio

        asyncio.run(self.handler.handle(update, DummyContext()))

        self.assertEqual(self.access_service.get_registration_mode(), "automatic")

    def test_users_menu_opens_without_context_error(self) -> None:
        message = DummyMessage("👥 Користувачі")
        update = SimpleNamespace(effective_message=message)

        import asyncio

        asyncio.run(self.handler.handle(update, DummyContext()))

        self.assertTrue(message.replies)
        self.assertEqual(message.replies[0][1].keyboard[-1][0].text, "⬅ Назад")

    def test_notification_toggle_responds_to_stateful_button_label(self) -> None:
        message = DummyMessage("🟢 Повідомлення адміну: Увімкнено")
        update = SimpleNamespace(effective_message=message)

        import asyncio

        asyncio.run(self.handler.handle(update, DummyContext()))

        self.assertFalse(self.access_service.get_notify_new_users())

    def test_admin_settings_regex_matches_stateful_button_labels(self) -> None:
        pattern = re.compile(get_admin_settings_menu_regex())

        self.assertIsNotNone(pattern.fullmatch("🟢 Реєстрація: Автоматична"))
        self.assertIsNotNone(pattern.fullmatch("🔴 Повідомлення адміну: Вимкнено"))
        self.assertIsNone(pattern.fullmatch("Щось інше"))

    def test_admin_settings_regex_matches_confirmation_buttons(self) -> None:
        pattern = re.compile(get_admin_settings_menu_regex())

        self.assertIsNotNone(pattern.fullmatch("✅ Так"))
        self.assertIsNotNone(pattern.fullmatch("❌ Ні"))

    def test_user_details_message_omits_empty_fields_and_uses_ukrainian_labels(self) -> None:
        user = User(
            id=1,
            telegram_id=12345,
            username="testuser",
            first_name="Іван",
            last_name=None,
            full_name=None,
            phone_number=None,
            role=UserRole.USER,
            status=UserStatus.ACTIVE,
            created_at="2025-01-01T00:00:00+00:00",
            updated_at="2025-01-01T00:00:00+00:00",
            last_activity_at=None,
            timezone=None,
            language_code="uk",
            is_premium=None,
            added_to_attachment_menu=None,
            allows_write_to_pm=None,
            can_join_groups=None,
            can_read_all_group_messages=None,
            supports_inline_queries=None,
        )

        message = self.users_service.build_user_details_message(user)

        self.assertIn("Ім'я", message)
        self.assertIn("Нік", message)
        self.assertIn("Роль", message)
        self.assertNotIn("Last name", message)
        self.assertNotIn("Premium", message)
        self.assertNotIn("Timezone", message)

    def test_user_button_label_uses_username_and_shortened_phone(self) -> None:
        user = User(
            id=2,
            telegram_id=777,
            username="eshil2",
            first_name="Олексій",
            last_name="Петренко",
            full_name="Олексій Петренко",
            phone_number="+380961234242",
            role=UserRole.USER,
            status=UserStatus.ACTIVE,
            created_at="2025-01-01T00:00:00+00:00",
            updated_at="2025-01-01T00:00:00+00:00",
        )

        label = self.users_service.build_user_button_label(user)

        self.assertEqual(label, "eshil2/+38096...242")

    def test_users_reply_keyboard_completes_ban_unban_delete_flow(self) -> None:
        target_id = self.user_repository.create(
            telegram_id=2,
            username="target",
            first_name="Користувач",
            last_name=None,
            phone_number="+380961234242",
            role=UserRole.USER,
            status=UserStatus.ACTIVE,
            created_at="2026-01-01T00:00:00+00:00",
        )
        self.settings_repository.create_default(target_id, "2026-01-01T00:00:00+00:00")
        context = DummyContext()

        self._send("👥 Користувачі", context)
        list_message = self._send("target/+38096...242", context)
        self.assertIn("Telegram ID: 2", list_message.replies[-1][0])

        self._send("🚫 Забанити", context)
        self._send("✅ Так", context)
        self.assertIs(self.users_service.find_user_by_id(target_id).status, UserStatus.BLOCKED)

        self._send("target/+38096...242", context)
        self._send("✅ Розбанити", context)
        self._send("✅ Так", context)
        self.assertIs(self.users_service.find_user_by_id(target_id).status, UserStatus.ACTIVE)

        self._send("target/+38096...242", context)
        self._send("🗑 Видалити користувача", context)
        self._send("✅ Так", context)

        self.assertIsNone(self.users_service.find_user_by_id(target_id))
        settings_row = self.database.execute(
            "SELECT 1 FROM user_settings WHERE user_id = ?",
            (target_id,),
        ).fetchone()
        self.assertIsNone(settings_row)
        self.assertNotIn(
            "target/+38096...242",
            [button.text for row in self._last_keyboard(context) for button in row],
        )

    def _send(self, text: str, context: DummyContext) -> DummyMessage:
        message = DummyMessage(text)
        import asyncio

        asyncio.run(self.handler.handle(SimpleNamespace(effective_message=message), context))
        if message.replies and message.replies[-1][1] is not None:
            context.user_data["last_keyboard"] = message.replies[-1][1].keyboard
        return message

    @staticmethod
    def _last_keyboard(context: DummyContext):
        return context.user_data.get("last_keyboard", [])


if __name__ == "__main__":
    unittest.main()
