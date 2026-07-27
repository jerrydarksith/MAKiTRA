import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from personal_bot.access.start_command_handler import StartCommandHandler
from personal_bot.core.enums import UserRole, UserStatus
from personal_bot.telegram.menus.main_menu import (
    get_main_menu_keyboard,
    get_main_menu_message,
    get_settings_menu_keyboard,
)


class StartCommandHandlerTests(unittest.TestCase):
    def test_start_command_sends_welcome_photo_and_menu(self) -> None:
        access_service = SimpleNamespace(
            find_user_by_telegram_id=lambda telegram_id: SimpleNamespace(
                id=1,
                telegram_id=telegram_id,
                username="tester",
                first_name="Test",
                last_name=None,
                role=UserRole.SUPER_ADMIN,
                status=UserStatus.ACTIVE,
            )
        )
        handler = StartCommandHandler(access_service)
        message = SimpleNamespace(
            reply_photo=AsyncMock(),
            reply_text=AsyncMock(),
        )
        update = SimpleNamespace(
            effective_user=SimpleNamespace(id=42),
            effective_message=message,
        )

        import asyncio

        asyncio.run(handler.handle(update, None))

        message.reply_photo.assert_awaited_once()
        args, kwargs = message.reply_photo.await_args
        self.assertEqual(args[0], "https://telegram.org/img/t_logo.png")
        self.assertIn("👋 Вітаю в MakiTra!", kwargs["caption"])
        self.assertIsNotNone(kwargs["reply_markup"])

    def test_main_menu_keyboard_contains_folder_and_settings_buttons(self) -> None:
        keyboard = get_main_menu_keyboard(UserRole.USER)
        buttons = [button.text for row in keyboard.keyboard for button in row]

        self.assertEqual(buttons, ["📝 Записи", "⚙️ Налаштування"])

    def test_settings_menu_includes_admin_section_for_super_admin(self) -> None:
        keyboard = get_settings_menu_keyboard(UserRole.SUPER_ADMIN, 5)
        buttons = [button.text for row in keyboard.keyboard for button in row]

        self.assertIn("🛡 Адміністрування", buttons)
        self.assertIn("👥 Користувачі (5)", buttons)

    def test_welcome_message_contains_expected_greeting(self) -> None:
        message = get_main_menu_message()

        self.assertIn("👋 Вітаю в MakiTra!", message)
        self.assertIn("Не тримай усе в голові.", message)
        self.assertNotIn("Головне меню.", message)


if __name__ == "__main__":
    unittest.main()
