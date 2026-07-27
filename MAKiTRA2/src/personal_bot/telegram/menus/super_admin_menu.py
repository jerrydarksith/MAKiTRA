from telegram import ReplyKeyboardMarkup


def super_admin_menu() -> ReplyKeyboardMarkup:
    keyboard = [
        ["👥 Користувачі"],
        ["⚙️ Налаштування"],
        ["📊 Статистика"],
    ]

    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
    )