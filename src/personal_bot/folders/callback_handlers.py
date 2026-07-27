from telegram import KeyboardButton, ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes, filters

from personal_bot.folders.service import FoldersService
from personal_bot.telegram.menus.folders_menu import (
    get_folder_delete_confirmation_keyboard,
    get_folder_list_keyboard,
    get_folder_menu_keyboard,
)
from personal_bot.telegram.menus.main_menu import get_main_menu_keyboard, get_main_menu_message
from personal_bot.users.service import UsersService


class FoldersMessageFilter(filters.MessageFilter):
    def __init__(self, handler: "FoldersMessageHandler") -> None:
        super().__init__()
        self._handler = handler

    def filter(self, message) -> bool:
        if message is None or message.text is None or message.from_user is None:
            return False

        text = message.text.strip()
        user_id = message.from_user.id
        command_texts = {
            "📝 Записи",
            "➕ Створити папку",
            "✏️ Перейменувати папку",
            "🗑 Видалити папку",
            "✅ Так",
            "❌ Ні",
        }

        if text == "⬅ Назад":
            return self._handler.is_active_session(user_id)

        if text in command_texts or text.startswith("📁 "):
            return True

        return (
            user_id in self._handler._pending_action_for_user
            or self._handler.is_active_session(user_id)
        )


class FoldersMessageHandler:
    def __init__(
        self,
        folders_service: FoldersService,
        users_service: UsersService,
    ) -> None:
        self._folders_service = folders_service
        self._users_service = users_service
        self._folder_session_for_user: dict[int, int | None] = {}
        self._pending_action_for_user: dict[int, str] = {}

    def get_filter(self) -> FoldersMessageFilter:
        return FoldersMessageFilter(self)

    def is_active_session(self, user_id: int) -> bool:
        return user_id in self._folder_session_for_user

    def _start_folder_session(self, user_id: int, folder_id: int | None = None) -> None:
        self._folder_session_for_user[user_id] = folder_id

    def _end_folder_session(self, user_id: int) -> None:
        self._folder_session_for_user.pop(user_id, None)
        self._pending_action_for_user.pop(user_id, None)

    def _current_folder_id(self, user_id: int) -> int | None:
        return self._folder_session_for_user.get(user_id)

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        del context
        message = update.effective_message

        if message is None or message.text is None:
            return

        telegram_user = message.from_user
        if telegram_user is None:
            return

        text = message.text.strip()
        user_id = telegram_user.id

        if text == "📝 Записи":
            self._start_folder_session(user_id, None)
            self._pending_action_for_user.pop(user_id, None)
            await self._show_folder_list(message, user_id)
            return

        if text == "➕ Створити папку":
            self._start_folder_session(user_id, self._current_folder_id(user_id))
            self._pending_action_for_user[user_id] = "create"
            await message.reply_text(
                "Введіть назву нової папки.",
                reply_markup=self._create_back_keyboard(),
            )
            return

        if text == "⬅ Назад" and self.is_active_session(user_id):
            self._end_folder_session(user_id)
            await message.reply_text(
                get_main_menu_message(),
                reply_markup=get_main_menu_keyboard(self._get_user_role(telegram_user)),
            )
            return

        if user_id in self._pending_action_for_user:
            action = self._pending_action_for_user[user_id]
            if action == "create":
                folder_name = text.strip()
                if folder_name:
                    self._folders_service.create_folder(owner_user_id=user_id, name=folder_name)
                self._pending_action_for_user.pop(user_id, None)
                self._start_folder_session(user_id, None)
                await self._show_folder_list(message, user_id)
                return

            if action == "rename":
                folder_id = self._current_folder_id(user_id)
                self._pending_action_for_user.pop(user_id, None)
                if folder_id is None:
                    self._end_folder_session(user_id)
                    return
                new_name = text.strip()
                if new_name:
                    self._folders_service.update_folder_name(folder_id, user_id, new_name)
                folder = self._folders_service.get_folder(folder_id, user_id)
                if folder is None:
                    self._end_folder_session(user_id)
                    return
                await message.reply_text(
                    self._folders_service.build_folder_page_message(folder),
                    reply_markup=get_folder_menu_keyboard(),
                )
                return

        if text.startswith("📁 "):
            folder_name = text[3:]
            folder = self._folders_service.find_root_folder_by_name(user_id, folder_name)
            if folder is None:
                return
            self._start_folder_session(user_id, folder.id)
            self._pending_action_for_user.pop(user_id, None)
            await message.reply_text(
                self._folders_service.build_folder_page_message(folder),
                reply_markup=get_folder_menu_keyboard(),
            )
            return

        if text == "✏️ Перейменувати папку":
            folder_id = self._current_folder_id(user_id)
            if folder_id is None:
                return
            self._pending_action_for_user[user_id] = "rename"
            await message.reply_text(
                "Введіть нову назву папки.",
                reply_markup=self._create_back_keyboard(),
            )
            return

        if text == "🗑 Видалити папку":
            folder_id = self._current_folder_id(user_id)
            if folder_id is None:
                return
            folder = self._folders_service.get_folder(folder_id, user_id)
            if folder is None:
                return
            await message.reply_text(
                f"Видалити папку \"{folder.name}\"?",
                reply_markup=get_folder_delete_confirmation_keyboard(),
            )
            return

        if text == "✅ Так":
            folder_id = self._current_folder_id(user_id)
            if folder_id is None:
                return
            folder = self._folders_service.get_folder(folder_id, user_id)
            if folder is None:
                self._end_folder_session(user_id)
                return
            if self._folders_service.can_delete_folder(folder_id, user_id):
                self._folders_service.delete_folder(folder_id, user_id)
                self._start_folder_session(user_id, None)
                await self._show_folder_list(message, user_id)
                return
            await message.reply_text(
                "Папка не порожня. Видалення непорожніх папок буде реалізовано пізніше.",
                reply_markup=get_folder_menu_keyboard(),
            )
            return

        if text == "❌ Ні":
            folder_id = self._current_folder_id(user_id)
            if folder_id is None:
                self._end_folder_session(user_id)
                return
            folder = self._folders_service.get_folder(folder_id, user_id)
            if folder is None:
                self._end_folder_session(user_id)
                return
            await message.reply_text(
                self._folders_service.build_folder_page_message(folder),
                reply_markup=get_folder_menu_keyboard(),
            )
            return

    async def _show_folder_list(self, message, user_id: int) -> None:
        await message.reply_text(
            self._folders_service.build_folder_list_message(user_id),
            reply_markup=get_folder_list_keyboard(self._folders_service.list_root_folders(user_id)),
        )

    def _get_user_role(self, from_user) -> None:
        if from_user is None:
            return None

        user = self._users_service.find_user_by_telegram_id(from_user.id)
        return user.role if user is not None else None

    @staticmethod
    def _create_back_keyboard() -> ReplyKeyboardMarkup:
        return ReplyKeyboardMarkup(
            [[KeyboardButton("⬅ Назад")]],
            resize_keyboard=True,
        )
