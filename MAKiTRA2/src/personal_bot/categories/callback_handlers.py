from telegram import KeyboardButton, ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes

from personal_bot.categories.service import CategoriesService
from personal_bot.telegram.menus.main_menu import (
    get_main_menu_message,
    get_super_admin_keyboard,
)


class CategoriesMessageHandler:
    def __init__(self, categories_service: CategoriesService) -> None:
        self._categories_service = categories_service

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        del context
        message = update.effective_message

        if message is None or message.text is None:
            return

        text = message.text.strip()

        if text == "📚 Категорії":
            await message.reply_text(
                self._categories_service.build_tree_message(owner_user_id=1),
                reply_markup=self._create_back_keyboard(),
            )
            return

        if text.startswith("create ") or text.startswith("створити "):
            category_name, parent_name = self._parse_creation_command(text)
            created_category = self._categories_service.create_category(
                owner_user_id=1,
                name=category_name,
                parent_id=None,
            )
            await message.reply_text(
                self._categories_service.build_creation_message(created_category),
                reply_markup=self._create_back_keyboard(),
            )
            return

        if text == "⬅ Назад":
            await message.reply_text(
                get_main_menu_message(),
                reply_markup=get_super_admin_keyboard(),
            )

    @staticmethod
    def _create_back_keyboard() -> ReplyKeyboardMarkup:
        return ReplyKeyboardMarkup(
            [[KeyboardButton("⬅ Назад")]],
            resize_keyboard=True,
        )

    @staticmethod
    def _parse_creation_command(text: str) -> tuple[str, str | None]:
        normalized_text = text.strip()
        parts = normalized_text.split()

        if len(parts) < 2:
            return "", None

        if parts[0].lower() in {"create", "створити"}:
            category_name = parts[1]
            parent_name = parts[2] if len(parts) > 2 else None
            return category_name, parent_name

        return "", None


class CategoriesCallbackHandler:
    def __init__(self, categories_service: CategoriesService) -> None:
        self._categories_service = categories_service

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        del context
        callback_query = update.callback_query

        if callback_query is None or callback_query.data is None:
            return

        if callback_query.data == "categories:back":
            await callback_query.answer()
            if callback_query.message is not None:
                await callback_query.message.reply_text(
                    get_main_menu_message(),
                    reply_markup=get_super_admin_keyboard(),
                )
