from telegram import KeyboardButton, ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes, filters
import traceback

from personal_bot.folders.service import FoldersService
from personal_bot.telegram.menus.folders_menu import (
    get_folder_delete_confirmation_keyboard,
    get_folder_menu_keyboard,
    get_folder_navigation_keyboard,
    get_record_type_keyboard,
)
from personal_bot.telegram.menus.main_menu import get_main_menu_keyboard, get_main_menu_message
from personal_bot.records.registry import RecordRegistry
from personal_bot.records.service import RecordsService
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
            "➕ Новий запис",
            "📁 Створити папку",
            "➕ Створити папку",
            "⚙️ Дії",
            "✏️ Перейменувати папку",
            "🗑️ Видалити папку",
            "🗑 Видалити папку",
            "✅ Так",
            "❌ Ні",
            "⬅️ Назад",
            "⬅ Назад",
            "⬅️ До папки",
            "◀️ Попередня",
            "▶️ Наступна",
            "🏠 Головне меню",
        }

        if text == "⬅️ Назад":
            return self._handler.is_active_session(user_id)

        if text in command_texts or text.startswith("📁 ") or text.startswith("📝 "):
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
        records_service: RecordsService,
        record_registry: RecordRegistry,
    ) -> None:
        self._folders_service = folders_service
        self._users_service = users_service
        self._records_service = records_service
        self._record_registry = record_registry
        self._folder_session_for_user: dict[int, int | None] = {}
        self._folder_page_for_user: dict[int, int] = {}
        self._pending_action_for_user: dict[int, str] = {}
        self._selected_record_type_for_user: dict[int, str] = {}

    def get_filter(self) -> FoldersMessageFilter:
        return FoldersMessageFilter(self)

    def is_active_session(self, user_id: int) -> bool:
        return user_id in self._folder_session_for_user

    def _start_folder_session(self, user_id: int, folder_id: int | None = None, page: int = 0) -> None:
        self._folder_session_for_user[user_id] = folder_id
        self._folder_page_for_user[user_id] = page

    def _end_folder_session(self, user_id: int) -> None:
        self._folder_session_for_user.pop(user_id, None)
        self._folder_page_for_user.pop(user_id, None)
        self._pending_action_for_user.pop(user_id, None)
        self._selected_record_type_for_user.pop(user_id, None)

    def _current_folder_id(self, user_id: int) -> int | None:
        return self._folder_session_for_user.get(user_id)

    def _current_page(self, user_id: int) -> int:
        return self._folder_page_for_user.get(user_id, 0)

    def _set_current_page(self, user_id: int, page: int) -> None:
        self._folder_page_for_user[user_id] = page

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
            self._start_folder_session(user_id, None, page=0)
            self._pending_action_for_user.pop(user_id, None)
            await self._show_folder_list(message, user_id)
            return

        if text == "📁 Створити папку" or text == "➕ Створити папку":
            self._start_folder_session(user_id, self._current_folder_id(user_id))
            self._pending_action_for_user[user_id] = "create"
            await message.reply_text(
                "Введіть назву нової папки.",
                reply_markup=self._create_back_keyboard(),
            )
            return

        if text == "⚙️ Дії":
            current_folder_id = self._current_folder_id(user_id)
            is_root = current_folder_id is None
            await message.reply_text(
                self._build_current_folder_message(user_id),
                reply_markup=get_folder_menu_keyboard(is_root=is_root),
            )
            return

        if text == "⬅️ До папки":
            current_folder_id = self._current_folder_id(user_id)
            if current_folder_id is None:
                await self._show_folder_list(message, user_id)
            else:
                await self._show_folder_page(message, user_id, current_folder_id)
            return

        if text == "➕ Новий запис":
            if self._current_folder_id(user_id) is None:
                return
            self._pending_action_for_user[user_id] = "select_record_type"
            await message.reply_text(
                "Оберіть тип запису.",
                reply_markup=get_record_type_keyboard(
                    self._record_registry.list_available_types()
                ),
            )
            return

        if text == "⬅️ Назад" or text == "⬅ Назад":
            if user_id in self._pending_action_for_user:
                self._pending_action_for_user.pop(user_id, None)
                self._selected_record_type_for_user.pop(user_id, None)
                current_folder_id = self._current_folder_id(user_id)
                if current_folder_id is not None:
                    await self._show_folder_page(message, user_id, current_folder_id)
                else:
                    await self._show_folder_list(message, user_id)
                return

            if self.is_active_session(user_id):
                current_folder_id = self._current_folder_id(user_id)
                if current_folder_id is None:
                    self._end_folder_session(user_id)
                    await message.reply_text(
                        get_main_menu_message(),
                        reply_markup=get_main_menu_keyboard(self._get_user_role(telegram_user)),
                    )
                    return

                owner_id = self._get_owner_id_for_user(user_id)
                if owner_id is None:
                    self._end_folder_session(user_id)
                    return

                current_folder = self._folders_service.get_folder(current_folder_id, owner_id)
                if current_folder is None:
                    self._start_folder_session(user_id, None, page=0)
                    await self._show_folder_list(message, user_id)
                    return

                parent_folder_id = current_folder.parent_id
                if parent_folder_id is None:
                    self._start_folder_session(user_id, None, page=0)
                    await self._show_folder_list(message, user_id)
                else:
                    self._start_folder_session(user_id, parent_folder_id, page=0)
                    await self._show_folder_page(message, user_id, parent_folder_id)
                return

        if text in {"◀️ Попередня", "▶️ Наступна"} and self.is_active_session(user_id):
            current_page = self._current_page(user_id)
            next_page = current_page - 1 if text == "◀️ Попередня" else current_page + 1
            self._set_current_page(user_id, max(0, next_page))
            current_folder_id = self._current_folder_id(user_id)
            if current_folder_id is None:
                await self._show_folder_list(message, user_id)
            else:
                await self._show_folder_page(message, user_id, current_folder_id)
            return

        if text == "🏠 Головне меню":
            if self.is_active_session(user_id):
                self._end_folder_session(user_id)
                await message.reply_text(
                    get_main_menu_message(),
                    reply_markup=get_main_menu_keyboard(self._get_user_role(telegram_user)),
                )
                return

        if user_id in self._pending_action_for_user:
            action = self._pending_action_for_user[user_id]
            if action == "select_record_type":
                if text not in self._record_registry.list_available_types():
                    await message.reply_text("Оберіть тип запису зі списку.")
                    return
                self._selected_record_type_for_user[user_id] = text
                self._pending_action_for_user[user_id] = "enter_record_text"
                await message.reply_text(
                    "Введіть текст запису.",
                    reply_markup=self._create_back_keyboard(),
                )
                return

            if action == "enter_record_text":
                folder_id = self._current_folder_id(user_id)
                type_code = self._selected_record_type_for_user.get(user_id)
                if folder_id is None or type_code is None:
                    self._end_folder_session(user_id)
                    return
                try:
                    user = self._users_service.find_user_by_telegram_id(user_id)
                    if user is None or getattr(user, "id", None) is None:
                        await message.reply_text(
                            "Внутрішній ідентифікатор користувача не знайдено. Зверніться до адміністратора.",
                        )
                        return

                    owner_id = user.id
                    self._records_service.create_record(
                        owner_user_id=owner_id,
                        folder_id=folder_id,
                        type_code=type_code,
                        name=text,
                        data={"value": text},
                    )
                except ValueError as error:
                    await message.reply_text(str(error))
                    return
                self._pending_action_for_user.pop(user_id, None)
                self._selected_record_type_for_user.pop(user_id, None)
                await self._show_folder_page(message, user_id, folder_id)
                return

            if action == "create":
                folder_name = text.strip()
                # debug prints as requested
                pending_action = self._pending_action_for_user.get(user_id)
                print("Поточний pending action.", pending_action)
                self._pending_action_for_user.pop(user_id, None)
                try:
                    print("Отримано текст від користувача.", text)
                    parent_folder_id = self._current_folder_id(user_id)
                    print("Значення parent_folder_id.", parent_folder_id)
                    user = self._users_service.find_user_by_telegram_id(user_id)
                    if user is None or getattr(user, "id", None) is None:
                        print("Значення owner_user_id.", None)
                        print("Перед reply_text().")
                        await message.reply_text(
                            "Внутрішній ідентифікатор користувача не знайдено. Зверніться до адміністратора.",
                            reply_markup=self._create_back_keyboard(),
                        )
                        print("Після reply_text().")
                        return

                    print("Значення owner_user_id.", user.id)
                    print("Перед викликом create_folder().")
                    self._folders_service.create_folder(
                        owner_user_id=user.id,
                        name=folder_name,
                        parent_id=parent_folder_id,
                    )
                    print("Після успішного create_folder().")
                except ValueError as error:
                    try:
                        print("Перед reply_text().")
                        await message.reply_text(str(error), reply_markup=self._create_back_keyboard())
                        print("Після reply_text().")
                        self._pending_action_for_user[user_id] = "create"
                        return
                    except Exception:
                        traceback.print_exc()
                        raise
                except Exception:
                    traceback.print_exc()
                    raise
                self._start_folder_session(user_id, self._current_folder_id(user_id), page=0)
                await self._show_folder_page(message, user_id, self._current_folder_id(user_id))
                return

            if action == "rename":
                folder_id = self._current_folder_id(user_id)
                self._pending_action_for_user.pop(user_id, None)
                if folder_id is None:
                    self._end_folder_session(user_id)
                    return
                new_name = text.strip()
                try:
                    user = self._users_service.find_user_by_telegram_id(user_id)
                    if user is None or getattr(user, "id", None) is None:
                        await message.reply_text(
                            "Внутрішній ідентифікатор користувача не знайдено. Зверніться до адміністратора.",
                            reply_markup=self._create_back_keyboard(),
                        )
                        return

                    owner_id = user.id
                    self._folders_service.update_folder_name(folder_id, owner_id, new_name)
                except ValueError as error:
                    await message.reply_text(str(error), reply_markup=self._create_back_keyboard())
                    self._pending_action_for_user[user_id] = "rename"
                    return
                await self._show_folder_page(message, user_id, folder_id)
                return

        if text.startswith("📁 "):
            folder_name = text[2:]
            current_folder_id = self._current_folder_id(user_id)
            user = self._users_service.find_user_by_telegram_id(user_id)
            if user is None or getattr(user, "id", None) is None:
                await message.reply_text(
                    "Внутрішній ідентифікатор користувача не знайдено. Зверніться до адміністратора.",
                    reply_markup=self._create_back_keyboard(),
                )
                return

            owner_id = user.id
            folder = self._folders_service.find_folder_by_name_and_parent(
                owner_user_id=owner_id,
                name=folder_name,
                parent_id=current_folder_id,
            )
            if folder is None:
                return
            self._start_folder_session(user_id, folder.id, page=0)
            self._pending_action_for_user.pop(user_id, None)
            await self._show_folder_page(message, user_id, folder.id)
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

        if text == "🗑️ Видалити папку":
            folder_id = self._current_folder_id(user_id)
            if folder_id is None:
                return
            user = self._users_service.find_user_by_telegram_id(user_id)
            if user is None or getattr(user, "id", None) is None:
                await message.reply_text(
                    "Внутрішній ідентифікатор користувача не знайдено. Зверніться до адміністратора.",
                    reply_markup=self._create_back_keyboard(),
                )
                return

            owner_id = user.id
            folder = self._folders_service.get_folder(folder_id, owner_id)
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
            user = self._users_service.find_user_by_telegram_id(user_id)
            if user is None or getattr(user, "id", None) is None:
                await message.reply_text(
                    "Внутрішній ідентифікатор користувача не знайдено. Зверніться до адміністратора.",
                    reply_markup=self._create_back_keyboard(),
                )
                return

            owner_id = user.id
            folder = self._folders_service.get_folder(folder_id, owner_id)
            if folder is None:
                self._end_folder_session(user_id)
                return
            if self._folders_service.can_delete_folder(folder_id, owner_id):
                self._folders_service.delete_folder(folder_id, owner_id)
                self._start_folder_session(user_id, None)
                await self._show_folder_list(message, user_id)
                return
            await message.reply_text(
                "Папка не порожня або містить записи. Видалення неможливе.",
                reply_markup=self._create_back_keyboard(),
            )
            return

        if text == "❌ Ні":
            folder_id = self._current_folder_id(user_id)
            if folder_id is None:
                self._end_folder_session(user_id)
                return
            await self._show_folder_page(message, user_id, folder_id)
            return

    async def _show_folder_list(self, message, user_id: int) -> None:
        telegram_user = message.from_user
        if telegram_user is None:
            return

        user = self._users_service.find_user_by_telegram_id(telegram_user.id)
        if user is None or getattr(user, "id", None) is None:
            await message.reply_text(
                "Внутрішній ідентифікатор користувача не знайдено. Зверніться до адміністратора.",
                reply_markup=self._create_back_keyboard(),
            )
            return

        owner_id = user.id
        current_page = self._current_page(user_id)

        await message.reply_text(
            self._build_root_message(),
            reply_markup=get_folder_navigation_keyboard(
                self._folders_service.list_root_folders(owner_id),
                [],
                is_root=True,
                page=current_page,
            ),
        )

    async def _show_folder_page(self, message, user_id: int, folder_id: int | None) -> None:
        if folder_id is None:
            await self._show_folder_list(message, user_id)
            return
        telegram_user = message.from_user
        if telegram_user is None:
            return

        user = self._users_service.find_user_by_telegram_id(telegram_user.id)
        if user is None or getattr(user, "id", None) is None:
            await message.reply_text(
                "Внутрішній ідентифікатор користувача не знайдено. Зверніться до адміністратора.",
                reply_markup=self._create_back_keyboard(),
            )
            return

        owner_id = user.id

        folder = self._folders_service.get_folder(folder_id, owner_id)
        if folder is None:
            self._end_folder_session(user_id)
            return

        current_page = self._current_page(user_id)
        self._start_folder_session(user_id, folder.id, page=current_page)
        child_folders = self._folders_service.list_child_folders(folder.id, owner_id)
        records = self._records_service.list_records(folder.id, owner_id)
        await message.reply_text(
            self._build_folder_message(folder),
            reply_markup=get_folder_navigation_keyboard(
                child_folders,
                records,
                is_root=False,
                page=current_page,
            ),
        )

    def _build_root_message(self) -> str:
        return "🧭 Мої записи"

    def _build_current_folder_message(self, user_id: int) -> str:
        current_folder_id = self._current_folder_id(user_id)
        if current_folder_id is None:
            return self._build_root_message()

        folder = self._folders_service.get_folder(current_folder_id, self._get_owner_id_for_user(user_id))
        if folder is None:
            return self._build_root_message()

        return self._build_folder_message(folder)

    def _build_folder_message(self, folder) -> str:
        path_components = [folder.name]
        parent_id = folder.parent_id
        while parent_id is not None:
            parent_folder = self._folders_service.get_folder(parent_id, folder.owner_user_id)
            if parent_folder is None:
                break
            path_components.append(parent_folder.name)
            parent_id = parent_folder.parent_id

        path_components.reverse()
        return f"🧭 Мої записи / {' / '.join(path_components)}"

    def _get_owner_id_for_user(self, user_id: int) -> int | None:
        user = self._users_service.find_user_by_telegram_id(user_id)
        return user.id if user is not None else None

    def _get_user_role(self, from_user) -> None:
        if from_user is None:
            return None

        user = self._users_service.find_user_by_telegram_id(from_user.id)
        return user.role if user is not None else None

    @staticmethod
    def _create_back_keyboard() -> ReplyKeyboardMarkup:
        return ReplyKeyboardMarkup(
            [[KeyboardButton("⬅️ Назад")]],
            resize_keyboard=True,
        )
