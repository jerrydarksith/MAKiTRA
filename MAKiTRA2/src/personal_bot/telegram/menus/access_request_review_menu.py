from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def create_access_request_review_menu(
    access_request_id: int,
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ Схвалити",
                    callback_data=f"access_request:approve:{access_request_id}",
                ),
                InlineKeyboardButton(
                    "❌ Відмовити",
                    callback_data=f"access_request:reject:{access_request_id}",
                ),
            ]
        ]
    )
