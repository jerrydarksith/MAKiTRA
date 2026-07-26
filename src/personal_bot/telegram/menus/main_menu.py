from telegram import KeyboardButton, ReplyKeyboardMarkup

from personal_bot.core.enums import UserRole


def get_main_menu_message() -> str:
    return (
        "👋 Вітаю в MakiTra!\n\n"
        "Не тримай усе в голові.\n"
        "Для цього є MakiTra.\n\n"
        "Я допоможу:\n\n"
        "📝 зберігати важливу інформацію;\n"
        "⏰ нагадувати про важливі події;\n"
        "📂 організовувати інформацію;\n"
        "🛒 вести списки;\n"
        "🚗 пам'ятати про автомобілі;\n"
        "💰 вести фінанси.\n\n"
        "Оберіть потрібний розділ у меню нижче."
    )


def get_main_menu_keyboard(role: UserRole | None = None) -> ReplyKeyboardMarkup:
    del role
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("📁 Папки")],
            [KeyboardButton("⚙️ Налаштування")],
        ],
        resize_keyboard=True,
    )


def get_settings_menu_keyboard(
    role: UserRole | None = None,
    users_count: int = 0,
) -> ReplyKeyboardMarkup:
    buttons = []

    if role is UserRole.SUPER_ADMIN:
        buttons.extend(
            [
                [KeyboardButton("🛡 Адміністрування")],
                [KeyboardButton(f"👥 Користувачі ({users_count})")],
                [KeyboardButton("📨 Заявки")],
            ]
        )

    buttons.append([KeyboardButton("⬅ Назад")])

    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)


def get_super_admin_keyboard() -> ReplyKeyboardMarkup:
    return get_main_menu_keyboard(UserRole.SUPER_ADMIN)