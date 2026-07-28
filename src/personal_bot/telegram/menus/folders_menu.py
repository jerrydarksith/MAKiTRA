from telegram import KeyboardButton, ReplyKeyboardMarkup

from personal_bot.core.entities.folder import Folder


# Folder menu helpers remain unchanged for folder actions.


def get_folder_list_keyboard(folders: list[Folder]) -> ReplyKeyboardMarkup:
    return get_folder_main_keyboard(folders, [], is_root=True)


def get_folder_main_keyboard(
    folders: list[Folder],
    records: list[object],
    is_root: bool = False,
    page: int = 0,
    page_size: int = 12,
) -> ReplyKeyboardMarkup:
    buttons: list[list[KeyboardButton]] = []

    for folder in folders:
        buttons.append([KeyboardButton(f"📁 {folder.name}")])

    for record in records:
        buttons.append([KeyboardButton(f"📝 {record.name}")])

    buttons.append([KeyboardButton("⚙️ Дії")])

    if not is_root:
        buttons.append([KeyboardButton("⬅️ Назад")])

    buttons.append([KeyboardButton("🏠 Головне меню")])

    if len(buttons) <= page_size:
        return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

    total_pages = (len(buttons) + page_size - 1) // page_size
    page_index = max(0, min(page, total_pages - 1))
    page_buttons = buttons[page_index * page_size : (page_index + 1) * page_size]

    nav_buttons: list[KeyboardButton] = []
    if page_index > 0:
        nav_buttons.append(KeyboardButton("◀️ Попередня"))
    if page_index < total_pages - 1:
        nav_buttons.append(KeyboardButton("▶️ Наступна"))
    if nav_buttons:
        page_buttons.append(nav_buttons)

    return ReplyKeyboardMarkup(page_buttons, resize_keyboard=True)


def get_folder_navigation_keyboard(
    folders: list[Folder],
    records: list[object],
    is_root: bool = False,
    page: int = 0,
    page_size: int = 12,
) -> ReplyKeyboardMarkup:
    return get_folder_main_keyboard(folders, records, is_root=is_root, page=page, page_size=page_size)


def get_folder_menu_keyboard(is_root: bool) -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton("➕ Новий запис")],
        [KeyboardButton("📁 Створити папку")],
    ]

    if not is_root:
        buttons.append([KeyboardButton("✏️ Перейменувати папку")])
        buttons.append([KeyboardButton("🗑️ Видалити папку")])

    buttons.append([KeyboardButton("⬅️ До папки")])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)


def get_record_type_keyboard(type_codes: tuple[str, ...]) -> ReplyKeyboardMarkup:
    buttons = [[KeyboardButton(type_code)] for type_code in type_codes]
    buttons.append([KeyboardButton("⬅️ Назад")])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)


def get_field_type_keyboard() -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton("📝 Текст")],
        [KeyboardButton("📄 Великий текст")],
        [KeyboardButton("🔢 Число")],
        [KeyboardButton("💰 Сума")],
        [KeyboardButton("📅 Дата")],
        [KeyboardButton("🕒 Дата і час")],
        [KeyboardButton("📞 Телефон")],
        [KeyboardButton("📧 Email")],
        [KeyboardButton("🌐 Посилання")],
        [KeyboardButton("✅ Так / Ні")],
        [KeyboardButton("⬅️ Назад")],
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)


def get_folder_delete_confirmation_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("✅ Так")],
            [KeyboardButton("❌ Ні")],
        ],
        resize_keyboard=True,
    )
