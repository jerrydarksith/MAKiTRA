from datetime import datetime
from telegram import KeyboardButton, ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes, filters
import traceback

from personal_bot.folders.service import FoldersService
from personal_bot.telegram.menus.folders_menu import (
    get_field_type_keyboard,
    get_folder_delete_confirmation_keyboard,
    get_folder_menu_keyboard,
    get_folder_navigation_keyboard,
    get_record_type_keyboard,
)
from personal_bot.telegram.menus.main_menu import get_main_menu_keyboard, get_main_menu_message
from personal_bot.telegram.menus.record_menu import (
    get_record_actions_keyboard,
    get_record_field_actions_keyboard,
    get_record_fields_keyboard,
    get_record_page_keyboard,
)
from personal_bot.records.registry import RecordRegistry
from personal_bot.records.service import RecordsService
from personal_bot.reminders.service import RemindersService
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
            "⬅️ До папки",
            "◀️ Попередня",
            "▶️ Наступна",
            "🏠 Головне меню",
        }

        if text in {"⬅️ Назад", "⬅ Назад"}:
            return self._handler.is_active_session(user_id) or user_id in self._handler._pending_action_for_user

        if text in {"✅ Так", "❌ Ні"}:
            return (
                user_id in self._handler._pending_action_for_user
                or user_id in self._handler._record_actions_for_user
            )

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
        reminders_service: RemindersService,
        record_registry: RecordRegistry,
    ) -> None:
        self._folders_service = folders_service
        self._users_service = users_service
        self._records_service = records_service
        self._reminders_service = reminders_service
        self._record_registry = record_registry
        self._folder_session_for_user: dict[int, int | None] = {}
        self._folder_page_for_user: dict[int, int] = {}
        self._pending_action_for_user: dict[int, str] = {}
        self._selected_record_type_for_user: dict[int, str] = {}
        self._selected_record_id_for_user: dict[int, int] = {}
        self._pending_field_data_for_user: dict[int, dict[str, object]] = {}
        self._record_actions_for_user: dict[int, str] = {}
        self._selected_field_for_user: dict[int, dict[str, object]] = {}
        self._pending_reminder_data_for_user: dict[int, dict[str, object]] = {}

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
        self._selected_field_for_user.pop(user_id, None)

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
            self._pending_action_for_user[user_id] = "enter_record_name"
            await message.reply_text(
                "Введіть назву запису.",
                reply_markup=self._create_back_keyboard(),
            )
            return

        if text == "⬅️ Назад" or text == "⬅ Назад":
            if user_id in self._pending_action_for_user:
                if self._pending_action_for_user[user_id] == "select_field_type":
                    self._pending_action_for_user.pop(user_id, None)
                    record_id = self._selected_record_id_for_user.get(user_id)
                    if record_id is not None:
                        await self._show_record_page(message, user_id, record_id)
                    else:
                        current_folder_id = self._current_folder_id(user_id)
                        if current_folder_id is not None:
                            await self._show_folder_page(message, user_id, current_folder_id)
                        else:
                            await self._show_folder_list(message, user_id)
                    return

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
            if action == "enter_record_name":
                folder_id = self._current_folder_id(user_id)
                if folder_id is None:
                    self._pending_action_for_user.pop(user_id, None)
                    return
                try:
                    user = self._users_service.find_user_by_telegram_id(user_id)
                    if user is None or getattr(user, "id", None) is None:
                        await message.reply_text(
                            "Внутрішній ідентифікатор користувача не знайдено. Зверніться до адміністратора.",
                        )
                        return

                    owner_id = user.id
                    available_types = self._record_registry.list_available_types()
                    type_code = available_types[0] if available_types else "short_text"
                    created_record = self._records_service.create_record(
                        owner_user_id=owner_id,
                        folder_id=folder_id,
                        type_code=type_code,
                        name=text.strip(),
                        data={"value": text.strip()},
                    )
                except ValueError as error:
                    await message.reply_text(str(error))
                    return
                self._pending_action_for_user.pop(user_id, None)
                self._selected_record_type_for_user.pop(user_id, None)
                self._selected_record_id_for_user[user_id] = created_record.id
                await self._show_record_page(message, user_id, created_record.id)
                return

            if action == "select_field_type":
                field_type = self._normalize_field_type(text)
                if field_type is None:
                    await message.reply_text("Оберіть тип поля зі списку.")
                    return

                default_field_name = self._get_default_field_name(field_type)
                if default_field_name is not None:
                    self._pending_field_data_for_user[user_id] = {"type": field_type, "name": default_field_name}
                    self._pending_action_for_user[user_id] = "enter_field_value"
                    await message.reply_text(
                        self._get_field_value_prompt(field_type),
                        reply_markup=self._create_back_keyboard(),
                    )
                    return

                self._pending_field_data_for_user[user_id] = {"type": field_type}
                self._pending_action_for_user[user_id] = "enter_field_name"
                await message.reply_text("Введіть назву поля.", reply_markup=self._create_back_keyboard())
                return

            if action == "enter_field_name":
                field_name = text.strip()
                if not field_name:
                    await message.reply_text("Назва поля не може бути порожньою.")
                    return
                pending_field = self._pending_field_data_for_user.get(user_id, {})
                pending_field["name"] = field_name
                self._pending_field_data_for_user[user_id] = pending_field
                self._pending_action_for_user[user_id] = "enter_field_value"
                await message.reply_text("Введіть значення.", reply_markup=self._create_back_keyboard())
                return

            if action == "enter_field_value":
                pending_field = self._pending_field_data_for_user.get(user_id, {})
                field_type = pending_field.get("type")
                field_name = pending_field.get("name")
                record_id = self._selected_record_id_for_user.get(user_id)
                if field_type is None or field_name is None or record_id is None:
                    self._pending_action_for_user.pop(user_id, None)
                    self._pending_field_data_for_user.pop(user_id, None)
                    return

                try:
                    user = self._users_service.find_user_by_telegram_id(user_id)
                    if user is None or getattr(user, "id", None) is None:
                        await message.reply_text(
                            "Внутрішній ідентифікатор користувача не знайдено. Зверніться до адміністратора.",
                        )
                        return

                    owner_id = user.id
                    record = self._records_service.get_record(record_id, owner_id)
                    if record is None:
                        return

                    existing_data = dict(record.payload or {})
                    fields = existing_data.get("fields")
                    if not isinstance(fields, list):
                        fields = []

                    field_id = self._build_field_id(record_id, len(fields))
                    fields.append({"id": field_id, "type": field_type, "name": field_name, "value": text.strip()})
                    existing_data["fields"] = fields
                    self._records_service.update_record(
                        record_id=record_id,
                        owner_user_id=owner_id,
                        data=existing_data,
                    )
                except ValueError as error:
                    await message.reply_text(str(error))
                    return

                self._pending_action_for_user.pop(user_id, None)
                self._pending_field_data_for_user.pop(user_id, None)
                await self._show_record_page(message, user_id, record_id)
                return

            if action == "edit_field_value":
                pending_field = self._pending_field_data_for_user.get(user_id, {})
                field_type = pending_field.get("field_type") or pending_field.get("type")
                record_id = pending_field.get("record_id")
                field_index = pending_field.get("field_index")
                field_id = pending_field.get("field_id")
                new_value = text.strip()

                if not new_value:
                    await message.reply_text("Значення не може бути порожнім.", reply_markup=self._create_back_keyboard())
                    self._pending_action_for_user[user_id] = "edit_field_value"
                    return

                validated_value = self._normalize_field_value(field_type, new_value)
                if validated_value is None:
                    await message.reply_text("Значення не може бути порожнім.", reply_markup=self._create_back_keyboard())
                    self._pending_action_for_user[user_id] = "edit_field_value"
                    return

                try:
                    user = self._users_service.find_user_by_telegram_id(user_id)
                    if user is None or getattr(user, "id", None) is None:
                        await message.reply_text(
                            "Внутрішній ідентифікатор користувача не знайдено. Зверніться до адміністратора.",
                            reply_markup=self._create_back_keyboard(),
                        )
                        return

                    owner_id = user.id
                    record = self._records_service.get_record(record_id, owner_id)
                    if record is None:
                        return

                    existing_data = dict(record.payload or {})
                    fields = existing_data.get("fields")
                    if not isinstance(fields, list):
                        fields = []

                    field_updated = False
                    for index, field in enumerate(fields):
                        if not isinstance(field, dict):
                            continue
                        current_field_id = field.get("id")
                        if field_id is not None and current_field_id == field_id:
                            field["value"] = validated_value
                            field_updated = True
                            break
                        if field_id is None and index == field_index:
                            field["value"] = validated_value
                            field_updated = True
                            break

                    if not field_updated:
                        existing_data["fields"] = fields
                        self._records_service.update_record(
                            record_id=record_id,
                            owner_user_id=owner_id,
                            data=existing_data,
                        )
                    else:
                        existing_data["fields"] = fields
                        self._records_service.update_record(
                            record_id=record_id,
                            owner_user_id=owner_id,
                            data=existing_data,
                        )
                except ValueError as error:
                    await message.reply_text(str(error), reply_markup=self._create_back_keyboard())
                    self._pending_action_for_user[user_id] = "edit_field_value"
                    return

                self._pending_action_for_user.pop(user_id, None)
                self._pending_field_data_for_user.pop(user_id, None)
                self._selected_field_for_user.pop(user_id, None)
                if record_id is not None:
                    await self._show_record_page(message, user_id, record_id)
                return

            if action == "enter_reminder_text":
                reminder_text = text.strip()
                if not reminder_text:
                    await message.reply_text("Текст нагадування не може бути порожнім.", reply_markup=self._create_back_keyboard())
                    return
                self._pending_reminder_data_for_user[user_id] = {"text": reminder_text}
                self._pending_action_for_user[user_id] = "enter_reminder_datetime"
                await message.reply_text(
                    "Введіть дату і час нагадування",
                    reply_markup=self._create_back_keyboard(),
                )
                return

            if action == "enter_reminder_datetime":
                reminder_datetime = text.strip()
                if not reminder_datetime:
                    await message.reply_text("Дата і час не можуть бути порожніми.", reply_markup=self._create_back_keyboard())
                    return
                try:
                    datetime.strptime(reminder_datetime, "%d.%m.%Y %H:%M")
                except ValueError:
                    await message.reply_text("Невірний формат. Використовуйте ДД.ММ.РРРР ГГ:ХХ", reply_markup=self._create_back_keyboard())
                    return
                pending_data = self._pending_reminder_data_for_user.get(user_id, {})
                reminder_text = pending_data.get("text")
                if not reminder_text:
                    self._pending_action_for_user.pop(user_id, None)
                    self._pending_reminder_data_for_user.pop(user_id, None)
                    return
                record_id = self._selected_record_id_for_user.get(user_id)
                if record_id is None:
                    self._pending_action_for_user.pop(user_id, None)
                    self._pending_reminder_data_for_user.pop(user_id, None)
                    return
                self._reminders_service.create_reminder(
                    record_id=record_id,
                    text=reminder_text,
                    remind_at=reminder_datetime,
                )
                self._pending_action_for_user.pop(user_id, None)
                self._pending_reminder_data_for_user.pop(user_id, None)
                await message.reply_text("Нагадування створено")
                await self._show_record_page(message, user_id, record_id)
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

            if action == "rename_record":
                record_id = self._selected_record_id_for_user.get(user_id)
                new_name = text.strip()
                if not new_name:
                    await message.reply_text(
                        "Назва запису не може бути порожньою.",
                        reply_markup=self._create_back_keyboard(),
                    )
                    self._pending_action_for_user[user_id] = "rename_record"
                    return

                try:
                    user = self._users_service.find_user_by_telegram_id(user_id)
                    if user is None or getattr(user, "id", None) is None:
                        await message.reply_text(
                            "Внутрішній ідентифікатор користувача не знайдено. Зверніться до адміністратора.",
                            reply_markup=self._create_back_keyboard(),
                        )
                        return

                    owner_id = user.id
                    record = self._records_service.get_record(record_id, owner_id)
                    if record is None:
                        self._pending_action_for_user.pop(user_id, None)
                        return

                    self._records_service.update_record(
                        record_id=record_id,
                        owner_user_id=owner_id,
                        data={"name": new_name, **dict(record.payload or {})},
                    )
                except ValueError as error:
                    await message.reply_text(str(error), reply_markup=self._create_back_keyboard())
                    self._pending_action_for_user[user_id] = "rename_record"
                    return

                self._pending_action_for_user.pop(user_id, None)
                if record_id is not None:
                    await self._show_record_page(message, user_id, record_id)
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

        if text == "📝 Редагувати поля":
            record_id = self._selected_record_id_for_user.get(user_id)
            if record_id is None:
                return
            user = self._users_service.find_user_by_telegram_id(user_id)
            if user is None or getattr(user, "id", None) is None:
                await message.reply_text(
                    "Внутрішній ідентифікатор користувача не знайдено. Зверніться до адміністратора.",
                    reply_markup=self._create_back_keyboard(),
                )
                return

            owner_id = user.id
            record = self._records_service.get_record(record_id, owner_id)
            if record is None:
                return

            payload = record.payload or {}
            fields = payload.get("fields") if isinstance(payload, dict) else None
            if not isinstance(fields, list):
                fields = []

            self._record_actions_for_user[user_id] = "record_fields_list"
            await message.reply_text(
                "Оберіть поле",
                reply_markup=get_record_fields_keyboard(fields),
            )
            return

        if text.startswith("📝 "):
            record_name = text[2:].strip()
            current_folder_id = self._current_folder_id(user_id)
            user = self._users_service.find_user_by_telegram_id(user_id)
            if user is None or getattr(user, "id", None) is None:
                await message.reply_text(
                    "Внутрішній ідентифікатор користувача не знайдено. Зверніться до адміністратора.",
                    reply_markup=self._create_back_keyboard(),
                )
                return

            owner_id = user.id
            if current_folder_id is None:
                return

            records = self._records_service.list_records(current_folder_id, owner_id)
            selected_record = next((record for record in records if record.name == record_name), None)
            if selected_record is None:
                return

            self._pending_action_for_user.pop(user_id, None)
            await self._show_record_page(message, user_id, selected_record.id)
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

        if text == "➕ Додати дані":
            record_id = self._selected_record_id_for_user.get(user_id)
            if record_id is None:
                return
            self._pending_action_for_user[user_id] = "select_field_type"
            await message.reply_text(
                "Оберіть тип поля.",
                reply_markup=get_field_type_keyboard(),
            )
            return

        if text == "⚙️ Дії із записом":
            record_id = self._selected_record_id_for_user.get(user_id)
            if record_id is None:
                return
            self._record_actions_for_user[user_id] = "record_actions"
            await message.reply_text(
                "Оберіть дію для запису.",
                reply_markup=get_record_actions_keyboard(),
            )
            return

        if text == "✏️ Перейменувати запис":
            record_id = self._selected_record_id_for_user.get(user_id)
            if record_id is None:
                return
            self._pending_action_for_user[user_id] = "rename_record"
            await message.reply_text(
                "Введіть нову назву запису.",
                reply_markup=self._create_back_keyboard(),
            )
            return

        if text == "✏️ Змінити значення":
            record_id = self._selected_record_id_for_user.get(user_id)
            selected_field = self._selected_field_for_user.get(user_id)
            if record_id is None or selected_field is None:
                return
            self._pending_action_for_user[user_id] = "edit_field_value"
            self._pending_field_data_for_user[user_id] = {
                "record_id": record_id,
                "field_id": selected_field.get("field_id"),
                "field_index": selected_field.get("field_index"),
                "field_type": selected_field.get("field_type"),
                "field_name": selected_field.get("field_name"),
            }
            await message.reply_text("Введіть нове значення поля.", reply_markup=self._create_back_keyboard())
            return

        if text == "📝 Перейменувати поле" or text == "🗑 Видалити поле":
            await message.reply_text("Функція буде реалізована пізніше.", reply_markup=self._create_back_keyboard())
            return

        if text == "⬅️ До списку полів" or text == "⬅️ Назад до запису":
            record_id = self._selected_record_id_for_user.get(user_id)
            if record_id is None:
                return
            self._record_actions_for_user.pop(user_id, None)
            await self._show_record_page(message, user_id, record_id)
            return

        if self._record_actions_for_user.get(user_id) == "record_actions" and text == "⬅️ Назад":
            self._record_actions_for_user.pop(user_id, None)
            record_id = self._selected_record_id_for_user.get(user_id)
            if record_id is None:
                return
            await self._show_record_page(message, user_id, record_id)
            return

        if self._record_actions_for_user.get(user_id) == "record_fields_list" and text != "⬅️ Назад":
            record_id = self._selected_record_id_for_user.get(user_id)
            user = self._users_service.find_user_by_telegram_id(user_id)
            if user is None or getattr(user, "id", None) is None:
                await message.reply_text(
                    "Внутрішній ідентифікатор користувача не знайдено. Зверніться до адміністратора.",
                    reply_markup=self._create_back_keyboard(),
                )
                return

            owner_id = user.id
            record = self._records_service.get_record(record_id, owner_id)
            if record is None:
                return

            payload = record.payload or {}
            fields = payload.get("fields") if isinstance(payload, dict) else None
            if not isinstance(fields, list):
                fields = []

            selected_field = None
            selected_index = None
            for index, field in enumerate(fields):
                if isinstance(field, dict) and field.get("name") == text:
                    selected_field = field
                    selected_index = index
                    break

            if selected_field is None:
                return

            self._selected_field_for_user[user_id] = {
                "field_id": self._build_field_id(record_id, selected_index, selected_field),
                "field_index": selected_index,
                "field_type": selected_field.get("type"),
                "field_name": selected_field.get("name"),
            }
            self._record_actions_for_user[user_id] = "record_field_actions"
            await message.reply_text(
                "Оберіть дію для поля.",
                reply_markup=get_record_field_actions_keyboard(),
            )
            return

        if text == "⏰ Нагадування":
            record_id = self._selected_record_id_for_user.get(user_id)
            if record_id is None:
                return
            self._pending_action_for_user[user_id] = "enter_reminder_text"
            await message.reply_text(
                "Введіть текст нагадування",
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
            self._pending_action_for_user[user_id] = "delete_folder"
            return

        if text == "🗑 Видалити запис":
            record_id = self._selected_record_id_for_user.get(user_id)
            if record_id is None:
                return
            await message.reply_text(
                "Видалити запис?",
                reply_markup=get_folder_delete_confirmation_keyboard(),
            )
            return

        if text == "✅ Так":
            if self._record_actions_for_user.get(user_id) == "record_actions":
                record_id = self._selected_record_id_for_user.get(user_id)
                if record_id is None:
                    return
                user = self._users_service.find_user_by_telegram_id(user_id)
                if user is None or getattr(user, "id", None) is None:
                    await message.reply_text(
                        "Внутрішній ідентифікатор користувача не знайдено. Зверніться до адміністратора.",
                        reply_markup=self._create_back_keyboard(),
                    )
                    return

                owner_id = user.id
                self._records_service.delete_record(record_id, owner_id)
                self._record_actions_for_user.pop(user_id, None)
                self._selected_record_id_for_user.pop(user_id, None)
                self._selected_field_for_user.pop(user_id, None)
                current_folder_id = self._current_folder_id(user_id)
                if current_folder_id is None:
                    await self._show_folder_list(message, user_id)
                else:
                    await self._show_folder_page(message, user_id, current_folder_id)
                return

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
            if self._record_actions_for_user.get(user_id) == "record_actions":
                record_id = self._selected_record_id_for_user.get(user_id)
                if record_id is None:
                    return
                self._record_actions_for_user.pop(user_id, None)
                await self._show_record_page(message, user_id, record_id)
                return

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

    async def _show_record_page(self, message, user_id: int, record_id: int) -> None:
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
        record = self._records_service.get_record(record_id, owner_id)
        if record is None:
            return

        self._selected_record_id_for_user[user_id] = record.id
        lines = [f"📄 {record.name}"]
        payload = record.payload or {}
        fields = payload.get("fields")
        if isinstance(fields, list) and fields:
            for field in fields:
                field_name = field.get("name", "")
                field_value = field.get("value", "")
                if field_name:
                    lines.append(f"\n📌 {field_name}")
                if field_value is not None:
                    lines.append(str(field_value))
        else:
            lines.append("")
            lines.append("Поки що дані відсутні.")

        await message.reply_text(
            "\n".join(lines),
            reply_markup=get_record_page_keyboard(),
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

    @staticmethod
    def _build_field_id(record_id: int | None, index: int, field: dict[str, object] | None = None) -> str:
        if isinstance(field, dict):
            existing_id = field.get("id")
            if isinstance(existing_id, str) and existing_id:
                return existing_id
            if isinstance(existing_id, int):
                return str(existing_id)
        if record_id is None:
            return f"field:{index}"
        return f"{record_id}:{index}"

    @staticmethod
    def _normalize_field_value(field_type: str | None, value: str) -> str | None:
        if value is None:
            return None

        normalized_value = value.strip()
        if not normalized_value:
            return None

        if field_type == "boolean":
            lower_value = normalized_value.lower()
            if lower_value in {"так", "true", "yes", "1"}:
                return "так"
            if lower_value in {"ні", "false", "no", "0"}:
                return "ні"
            return None

        if field_type in {"number", "money"}:
            try:
                float(normalized_value.replace(",", "."))
            except ValueError:
                return None

        return normalized_value

    @staticmethod
    def _normalize_field_type(text: str) -> str | None:
        field_type_map = {
            "📝 Текст": "text",
            "📄 Великий текст": "long_text",
            "🔢 Число": "number",
            "💰 Сума": "money",
            "📅 Дата": "date",
            "🕒 Дата і час": "datetime",
            "📞 Телефон": "phone",
            "📧 Email": "email",
            "🌐 Посилання": "url",
            "✅ Так / Ні": "boolean",
        }
        return field_type_map.get(text)

    @staticmethod
    def _get_default_field_name(field_type: str) -> str | None:
        default_field_names = {
            "money": "Сума",
            "date": "Дата",
            "datetime": "Дата і час",
            "phone": "Телефон",
            "email": "Email",
            "url": "Посилання",
            "boolean": "Так / Ні",
        }
        return default_field_names.get(field_type)

    @staticmethod
    def _get_field_value_prompt(field_type: str) -> str:
        prompts = {
            "money": "Введіть суму.",
            "date": "Введіть дату.",
            "datetime": "Введіть дату і час.",
            "phone": "Введіть телефон.",
            "email": "Введіть email.",
            "url": "Введіть посилання.",
            "boolean": "Введіть так / ні.",
        }
        return prompts.get(field_type, "Введіть значення.")
