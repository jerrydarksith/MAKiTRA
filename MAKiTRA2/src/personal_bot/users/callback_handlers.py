from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes

from personal_bot.core.enums import UserRole
from personal_bot.telegram.menus.main_menu import (
    get_main_menu_keyboard,
    get_main_menu_message,
    get_settings_menu_keyboard,
)
from personal_bot.users.service import UsersService


class UsersMessageHandler:
    def __init__(self, users_service: UsersService) -> None:
        self._users_service = users_service

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        del context
        message = update.effective_message

        if message is None or message.text is None:
            return

        text = message.text.strip()

        if text == "📁 Папки":
            await message.reply_text(
                "📁 Папки\n\n"
                "Основна структура MakiTra — це папки."
                " У майбутньому всередині папок будуть документи, нотатки, нагадування,"
                " фінанси, фотографії та файли.",
                reply_markup=self._create_back_keyboard(),
            )
            return

        if text in {"⚙️ Налаштування", "🛡 Адміністрування"}:
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
            await self._show_users_page(message, page=1)
            return

        if text == "⬅ Назад":
            await message.reply_text(
                get_main_menu_message(),
                reply_markup=get_main_menu_keyboard(self._get_user_role(message)),
            )

    def _get_user_role(self, message) -> UserRole | None:
        if message is None or message.from_user is None:
            return None

        user = self._users_service.find_user_by_telegram_id(message.from_user.id)
        return user.role if user is not None else None

    @staticmethod
    def _create_back_keyboard() -> ReplyKeyboardMarkup:
        return ReplyKeyboardMarkup(
            [[KeyboardButton("⬅ Назад")]],
            resize_keyboard=True,
        )

    async def _show_users_page(self, message, page: int) -> None:
        users_page = self._users_service.get_active_users_page(page=page, page_size=5)
        await message.reply_text(
            self._users_service.build_users_page_message(users_page),
            reply_markup=self._build_pagination_keyboard(users_page),
        )

    @staticmethod
    def _build_pagination_keyboard(users_page) -> InlineKeyboardMarkup:
        buttons = []

        if users_page.page > 1:
            buttons.append(
                InlineKeyboardButton("⬅", callback_data=f"users:page:{users_page.page - 1}")
            )

        buttons.append(InlineKeyboardButton("⬅ Назад", callback_data="users:back"))

        if users_page.page < users_page.total_pages:
            buttons.append(
                InlineKeyboardButton("➡", callback_data=f"users:page:{users_page.page + 1}")
            )

        return InlineKeyboardMarkup([buttons])


class UsersCallbackHandler:
    def __init__(self, users_service: UsersService) -> None:
        self._users_service = users_service

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        del context
        callback_query = update.callback_query

        if callback_query is None or callback_query.data is None:
            return

        if callback_query.data == "users:back":
            await callback_query.answer()
            if callback_query.message is not None:
                await callback_query.message.reply_text(
                    get_main_menu_message(),
                    reply_markup=get_main_menu_keyboard(self._get_user_role(callback_query.from_user)),
                )
            return

        if callback_query.data.startswith("users:page:"):
            page_value = callback_query.data.split(":")[-1]
            try:
                page = int(page_value)
            except ValueError:
                return

            users_page = self._users_service.get_active_users_page(page=page, page_size=5)
            await callback_query.answer()
            if callback_query.message is not None:
                await callback_query.edit_message_text(
                    self._users_service.build_users_page_message(users_page),
                    reply_markup=self._build_pagination_keyboard(users_page),
                )

    def _get_user_role(self, from_user) -> UserRole | None:
        if from_user is None:
            return None

        user = self._users_service.find_user_by_telegram_id(from_user.id)
        return user.role if user is not None else None

    @staticmethod
    def _build_pagination_keyboard(users_page) -> InlineKeyboardMarkup:
        buttons = []

        if users_page.page > 1:
            buttons.append(
                InlineKeyboardButton("⬅", callback_data=f"users:page:{users_page.page - 1}")
            )

        buttons.append(InlineKeyboardButton("⬅ Назад", callback_data="users:back"))

        if users_page.page < users_page.total_pages:
            buttons.append(
                InlineKeyboardButton("➡", callback_data=f"users:page:{users_page.page + 1}")
            )

        return InlineKeyboardMarkup([buttons])
