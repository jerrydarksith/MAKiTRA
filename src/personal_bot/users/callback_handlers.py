from telegram import KeyboardButton, ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes

from personal_bot.access.service import AccessService
from personal_bot.core.enums import UserRole, UserStatus
from personal_bot.telegram.menus.main_menu import (
    get_main_menu_keyboard,
    get_main_menu_message,
    get_settings_menu_keyboard,
)
from personal_bot.telegram.menus.super_admin_menu import (
    get_admin_settings_menu_keyboard,
    get_notify_new_users_button_text,
    get_registration_mode_button_text,
)
from personal_bot.telegram.menus.users_menu import get_user_management_keyboard
from personal_bot.users.service import UsersService


class UsersMessageHandler:
    def __init__(self, users_service: UsersService, access_service: AccessService) -> None:
        self._users_service = users_service
        self._access_service = access_service

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        message = update.effective_message

        if message is None or message.text is None:
            return

        text = message.text.strip()

        current_menu = context.user_data.get("current_menu")
        if current_menu in {"admin_settings", "users_list", "user_manage"} and not self._is_super_admin(message):
            await message.reply_text("Недостатньо прав для цієї дії.")
            return

        if await self._handle_back_navigation(message, context):
            return

        if text == "📁 Папки":
            await message.reply_text(
                "📁 Папки\n\n"
                "Основна структура MakiTra — це папки."
                " У майбутньому всередині папок будуть документи, нотатки, нагадування,"
                " фінанси, фотографії та файли.",
                reply_markup=self._create_back_keyboard(),
            )
            return

        if text == "🛡 Адміністрування":
            context.user_data["current_menu"] = "admin_settings"
            await self._show_admin_settings_menu(message)
            return

        if text == "⚙️ Налаштування":
            context.user_data["current_menu"] = "settings"
            user_role = self._get_user_role(message)
            await message.reply_text(
                "⚙️ Налаштування",
                reply_markup=get_settings_menu_keyboard(
                    user_role,
                    self._users_service.get_active_users_count(),
                ),
            )
            return

        if text == "📨 Заявки":
            await message.reply_text(
                "📨 Заявки\n\nПоки що цей розділ ще не реалізовано.",
                reply_markup=self._create_back_keyboard(),
            )
            return

        if text == "👥 Користувачі" or text.startswith("👥 Користувачі ("):
            if not self._is_super_admin(message):
                await message.reply_text("Недостатньо прав для цієї дії.")
                return
            context.user_data["current_menu"] = "users_list"
            await self._show_users_page(message, page=1, context=context)
            return

        if text in {
            get_registration_mode_button_text("automatic"),
            get_registration_mode_button_text("manual"),
            "Режим реєстрації: Автоматична",
            "Режим реєстрації: Через підтвердження",
        }:
            previous_mode = self._access_service.get_registration_mode()
            new_mode = "automatic" if previous_mode != "automatic" else "manual"
            self._access_service.set_registration_mode(new_mode)
            await message.reply_text(
                "✅ Режим реєстрації змінено.\n\n"
                "Було:\n"
                f"{'Автоматична.' if previous_mode == 'automatic' else 'Через підтвердження.'}\n\n"
                "Стало:\n"
                f"{'Автоматична.' if new_mode == 'automatic' else 'Через підтвердження.'}"
            )
            context.user_data["current_menu"] = "admin_settings"
            await self._show_admin_settings_menu(message)
            return

        if text in {
            get_notify_new_users_button_text(True),
            get_notify_new_users_button_text(False),
            "Повідомлення адміну: Увімкнено",
            "Повідомлення адміну: Вимкнено",
        }:
            previous_value = self._access_service.get_notify_new_users()
            new_value = not previous_value
            self._access_service.set_notify_new_users(new_value)
            await message.reply_text(
                "✅ Налаштування повідомлень змінено.\n\n"
                "Було:\n"
                f"{'Увімкнено.' if previous_value else 'Вимкнено.'}\n\n"
                "Стало:\n"
                f"{'Увімкнено.' if new_value else 'Вимкнено.'}"
            )
            context.user_data["current_menu"] = "admin_settings"
            await self._show_admin_settings_menu(message)
            return

        if context.user_data.get("current_menu") == "users_list" and text != "⬅ Назад":
            user_id = context.user_data.get("user_button_map", {}).get(text)
            if user_id is None and text.startswith("👤 user:"):
                try:
                    user_id = int(text.split(":", 1)[1])
                except ValueError:
                    user_id = None

            if user_id is None:
                return

            user = self._users_service.find_user_by_id(user_id)
            if user is None:
                return
            context.user_data["selected_user_id"] = user_id
            context.user_data["current_menu"] = "user_manage"
            await message.reply_text(
                self._users_service.build_user_details_message(user),
                reply_markup=get_user_management_keyboard(),
            )
            return

        if text == "⬅ Попередня" and context.user_data.get("current_menu") == "users_list":
            current_page = int(context.user_data.get("users_page", 1))
            await self._show_users_page(message, page=max(1, current_page - 1), context=context)
            return

        if text == "➡ Наступна" and context.user_data.get("current_menu") == "users_list":
            current_page = int(context.user_data.get("users_page", 1))
            await self._show_users_page(message, page=current_page + 1, context=context)
            return

        if text == "🗑 Видалити користувача" and context.user_data.get("current_menu") == "user_manage":
            user_id = context.user_data.get("selected_user_id")
            if user_id is None:
                return
            await message.reply_text(
                "Ви дійсно бажаєте повністю видалити цього користувача?",
                reply_markup=ReplyKeyboardMarkup(
                    [[KeyboardButton("✅ Так"), KeyboardButton("❌ Ні")]],
                    resize_keyboard=True,
                ),
            )
            context.user_data["pending_action"] = "delete_user"
            return

        if text == "🚫 Забанити" and context.user_data.get("current_menu") == "user_manage":
            user_id = context.user_data.get("selected_user_id")
            if user_id is None:
                return
            await message.reply_text(
                "Забанити цього користувача?",
                reply_markup=ReplyKeyboardMarkup(
                    [[KeyboardButton("✅ Так"), KeyboardButton("❌ Ні")]],
                    resize_keyboard=True,
                ),
            )
            context.user_data["pending_action"] = "block_user"
            return

        if text == "✅ Розбанити" and context.user_data.get("current_menu") == "user_manage":
            user_id = context.user_data.get("selected_user_id")
            if user_id is None:
                return
            await message.reply_text(
                "Розбанити цього користувача?",
                reply_markup=ReplyKeyboardMarkup(
                    [[KeyboardButton("✅ Так"), KeyboardButton("❌ Ні")]],
                    resize_keyboard=True,
                ),
            )
            context.user_data["pending_action"] = "unblock_user"
            return

        if text == "✅ Так" and context.user_data.get("pending_action"):
            pending_action = context.user_data.get("pending_action")
            user_id = context.user_data.get("selected_user_id")
            if pending_action == "delete_user" and user_id is not None:
                self._users_service.delete_user(user_id)
                context.user_data.pop("selected_user_id", None)
                context.user_data.pop("pending_action", None)
                context.user_data["current_menu"] = "users_list"
                await message.reply_text("✅ Користувача успішно видалено.")
                await self._show_users_page(message, page=context.user_data.get("users_page", 1), context=context)
                return
            if pending_action == "block_user" and user_id is not None:
                self._users_service.block_user(user_id)
                context.user_data.pop("pending_action", None)
                context.user_data["current_menu"] = "users_list"
                await message.reply_text("✅ Користувача заблоковано.")
                await self._show_users_page(message, page=context.user_data.get("users_page", 1), context=context)
                return
            if pending_action == "unblock_user" and user_id is not None:
                self._users_service.unblock_user(user_id)
                context.user_data.pop("pending_action", None)
                context.user_data["current_menu"] = "users_list"
                await message.reply_text("✅ Користувача розблоковано.")
                await self._show_users_page(message, page=context.user_data.get("users_page", 1), context=context)
                return

        if text == "❌ Ні" and context.user_data.get("pending_action"):
            context.user_data.pop("pending_action", None)
            user_id = context.user_data.get("selected_user_id")
            if user_id is not None:
                user = self._users_service.find_user_by_id(user_id)
                if user is not None:
                    context.user_data["current_menu"] = "user_manage"
                    await message.reply_text(
                        self._users_service.build_user_details_message(user),
                        reply_markup=get_user_management_keyboard(),
                    )
                return


    async def _handle_back_navigation(self, message, context) -> bool:
        if message.text.strip() not in {"⬅ Назад", "⬅️ Назад"}:
            return False

        current_menu = context.user_data.get("current_menu")
        if current_menu == "user_manage":
            context.user_data.pop("pending_action", None)
            context.user_data.pop("selected_user_id", None)
            context.user_data["current_menu"] = "users_list"
            await self._show_users_page(
                message,
                page=context.user_data.get("users_page", 1),
                context=context,
            )
            return True

        if current_menu in {"admin_settings", "users_list"}:
            context.user_data.pop("user_button_map", None)
            context.user_data.pop("selected_user_id", None)
            context.user_data["current_menu"] = "settings"
            await message.reply_text(
                "⚙️ Налаштування",
                reply_markup=get_settings_menu_keyboard(
                    self._get_user_role(message),
                    self._users_service.get_active_users_count(),
                ),
            )
            return True

        if current_menu == "settings":
            context.user_data["current_menu"] = "main"
            await message.reply_text(
                get_main_menu_message(),
                reply_markup=get_main_menu_keyboard(self._get_user_role(message)),
            )
            return True

        return False

    def _get_user_role(self, message) -> UserRole | None:
        if message is None or message.from_user is None:
            return None

        user = self._users_service.find_user_by_telegram_id(message.from_user.id)
        return user.role if user is not None else None

    def _is_super_admin(self, message) -> bool:
        user = self._users_service.find_user_by_telegram_id(message.from_user.id)
        return (
            user is not None
            and user.role is UserRole.SUPER_ADMIN
            and user.status is UserStatus.ACTIVE
        )

    @staticmethod
    def _create_back_keyboard() -> ReplyKeyboardMarkup:
        return ReplyKeyboardMarkup(
            [[KeyboardButton("⬅ Назад")]],
            resize_keyboard=True,
        )

    async def _show_users_page(self, message, page: int, context=None) -> None:
        users_page = self._users_service.get_users_page(page=page, page_size=10)
        if context is not None and hasattr(context, "user_data"):
            context.user_data["users_page"] = users_page.page

        buttons = []
        user_button_map = {}
        for user in users_page.users:
            label = self._users_service.build_user_button_label(user)
            user_button_map[label] = user.id
            buttons.append([KeyboardButton(label)])

        if users_page.total_pages > 1:
            pagination_row = []
            if users_page.page > 1:
                pagination_row.append(KeyboardButton("⬅ Попередня"))
            if users_page.page < users_page.total_pages:
                pagination_row.append(KeyboardButton("➡ Наступна"))
            buttons.append(pagination_row)

        buttons.append([KeyboardButton("⬅ Назад")])

        if context is not None and hasattr(context, "user_data"):
            context.user_data["user_button_map"] = user_button_map
        keyboard = ReplyKeyboardMarkup(buttons, resize_keyboard=True)
        await message.reply_text(
            self._users_service.build_users_page_message(users_page),
            reply_markup=keyboard,
        )

    async def _show_admin_settings_menu(self, message) -> None:
        await message.reply_text(
            "🛡 Адміністрування",
            reply_markup=get_admin_settings_menu_keyboard(
                self._access_service.get_registration_mode(),
                self._access_service.get_notify_new_users(),
            ),
        )

