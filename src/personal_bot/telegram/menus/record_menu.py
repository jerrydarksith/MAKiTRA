from telegram import KeyboardButton, ReplyKeyboardMarkup


def get_record_page_keyboard() -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton("➕ Додати дані")],
        [KeyboardButton("⚙️ Дії із записом")],
        [KeyboardButton("⬅️ До папки")],
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)


def get_record_actions_keyboard() -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton("✏️ Перейменувати запис")],
        [KeyboardButton("📝 Редагувати поля")],
        [KeyboardButton("⏰ Нагадування")],
        [KeyboardButton("🗑 Видалити запис")],
        [KeyboardButton("⬅️ Назад до запису")],
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)


def get_record_fields_keyboard(fields: list[dict[str, object]]) -> ReplyKeyboardMarkup:
    buttons: list[list[KeyboardButton]] = []
    for field in fields:
        name = field.get("name") if isinstance(field, dict) else None
        button_text = str(name) if name is not None else "Поле"
        buttons.append([KeyboardButton(button_text)])

    buttons.append([KeyboardButton("⬅️ Назад")])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)


def get_record_field_actions_keyboard() -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton("✏️ Змінити значення")],
        [KeyboardButton("📝 Перейменувати поле")],
        [KeyboardButton("🗑 Видалити поле")],
        [KeyboardButton("⬅️ До списку полів")],
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)
