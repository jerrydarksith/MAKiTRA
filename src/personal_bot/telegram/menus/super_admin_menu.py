from telegram import KeyboardButton, ReplyKeyboardMarkup


def get_registration_mode_button_text(registration_mode: str) -> str:
    return (
        "🟢 Реєстрація: Автоматична"
        if registration_mode == "automatic"
        else "🔴 Реєстрація: Через підтвердження"
    )


def get_notify_new_users_button_text(notify_new_users: bool) -> str:
    return (
        "🟢 Повідомлення адміну: Увімкнено"
        if notify_new_users
        else "🔴 Повідомлення адміну: Вимкнено"
    )


def get_admin_settings_menu_keyboard(
    registration_mode: str,
    notify_new_users: bool,
) -> ReplyKeyboardMarkup:
    registration_button = get_registration_mode_button_text(registration_mode)
    notification_button = get_notify_new_users_button_text(notify_new_users)

    return ReplyKeyboardMarkup(
        [
            [KeyboardButton(registration_button)],
            [KeyboardButton(notification_button)],
            [KeyboardButton("⬅️ Назад")],
        ],
        resize_keyboard=True,
    )