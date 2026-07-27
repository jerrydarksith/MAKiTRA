from telegram import KeyboardButton, ReplyKeyboardMarkup

from personal_bot.core.entities.folder import Folder


def get_folder_list_keyboard(folders: list[Folder]) -> ReplyKeyboardMarkup:
    buttons = [[KeyboardButton(f"📁 {folder.name}")] for folder in folders]
    buttons.append([KeyboardButton("➕ Створити папку")])
    buttons.append([KeyboardButton("⬅ Назад")])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)


def get_folder_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("➕ Новий запис")],
            [KeyboardButton("➕ Створити папку")],
            [KeyboardButton("✏️ Перейменувати папку")],
            [KeyboardButton("🗑 Видалити папку")],
            [KeyboardButton("⬅ Назад")],
        ],
        resize_keyboard=True,
    )


def get_record_type_keyboard(type_codes: tuple[str, ...]) -> ReplyKeyboardMarkup:
    buttons = [[KeyboardButton(type_code)] for type_code in type_codes]
    buttons.append([KeyboardButton("⬅ Назад")])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)


def get_folder_delete_confirmation_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("✅ Так")],
            [KeyboardButton("❌ Ні")],
        ],
        resize_keyboard=True,
    )
