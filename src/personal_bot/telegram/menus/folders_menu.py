from telegram import KeyboardButton, ReplyKeyboardMarkup

from personal_bot.core.entities.folder import Folder


def get_folder_list_keyboard(folders: list[Folder]) -> ReplyKeyboardMarkup:
    return get_folder_navigation_keyboard(folders, [])


def get_folder_navigation_keyboard(folders: list[Folder], records: list[object]) -> ReplyKeyboardMarkup:
    buttons: list[list[KeyboardButton]] = []

    for folder in folders:
        buttons.append([KeyboardButton(f"📁 {folder.name}")])

    for record in records:
        buttons.append([KeyboardButton(f"📝 {record.name}")])

    buttons.append([KeyboardButton("➕ Новий запис")])
    buttons.append([KeyboardButton("📁 Створити папку")])
    buttons.append([KeyboardButton("✏️ Перейменувати папку")])
    buttons.append([KeyboardButton("🗑️ Видалити папку")])
    buttons.append([KeyboardButton("⬅️ Назад")])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)


def get_folder_menu_keyboard() -> ReplyKeyboardMarkup:
    return get_folder_navigation_keyboard([], [])


def get_record_type_keyboard(type_codes: tuple[str, ...]) -> ReplyKeyboardMarkup:
    buttons = [[KeyboardButton(type_code)] for type_code in type_codes]
    buttons.append([KeyboardButton("⬅️ Назад")])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)


def get_folder_delete_confirmation_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("✅ Так")],
            [KeyboardButton("❌ Ні")],
        ],
        resize_keyboard=True,
    )
