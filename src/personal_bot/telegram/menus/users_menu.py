from telegram import KeyboardButton, ReplyKeyboardMarkup


def get_users_list_keyboard(user_labels: list[str]) -> ReplyKeyboardMarkup:
    buttons = [[KeyboardButton(label)] for label in user_labels]
    buttons.append([KeyboardButton("⬅️ Назад")])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)


def get_user_management_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("🗑 Видалити користувача")],
            [KeyboardButton("🚫 Забанити")],
            [KeyboardButton("✅ Розбанити")],
            [KeyboardButton("⬅ Назад")],
        ],
        resize_keyboard=True,
    )


def get_users_pagination_keyboard(page: int, total_pages: int) -> ReplyKeyboardMarkup:
    buttons: list[list[KeyboardButton]] = []
    row: list[KeyboardButton] = []

    if page > 1:
        row.append(KeyboardButton("⬅ Попередня"))
    if page < total_pages:
        row.append(KeyboardButton("➡ Наступна"))

    if row:
        buttons.append(row)

    buttons.append([KeyboardButton("⬅ Назад")])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)
