from telegram import Update
from telegram.ext import ContextTypes

from personal_bot.access.service import AccessService
from personal_bot.core.enums import AccessRequestReviewResult


class AccessRequestCallbackHandler:
    def __init__(self, access_service: AccessService) -> None:
        self._access_service = access_service

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        callback_query = update.callback_query
        telegram_user = update.effective_user

        if callback_query is None or callback_query.data is None or telegram_user is None:
            return

        action, access_request_id = self._parse_callback_data(callback_query.data)

        if action == "approve":
            review_outcome = self._access_service.approve_access_request(
                access_request_id,
                telegram_user.id,
            )
        else:
            review_outcome = self._access_service.reject_access_request(
                access_request_id,
                telegram_user.id,
            )

        if review_outcome.result is AccessRequestReviewResult.UNAUTHORIZED:
            await callback_query.answer(
                "Недостатньо прав для цієї дії.",
                show_alert=True,
            )
            return

        if review_outcome.result is AccessRequestReviewResult.NOT_FOUND:
            await callback_query.answer("Заявку не знайдено.", show_alert=True)
            return

        if review_outcome.result is AccessRequestReviewResult.ALREADY_PROCESSED:
            await callback_query.answer(
                "Ця заявка вже була оброблена.",
                show_alert=True,
            )
            return

        if review_outcome.access_request is None:
            return

        if review_outcome.result is AccessRequestReviewResult.APPROVED:
            await context.bot.send_message(
                chat_id=review_outcome.access_request.telegram_id,
                text="Вашу заявку підтверджено. Доступ до бота відкрито.",
            )
            await callback_query.answer("Заявку схвалено.")
            await callback_query.edit_message_reply_markup(reply_markup=None)
            return

        await context.bot.send_message(
            chat_id=review_outcome.access_request.telegram_id,
            text="Вашу заявку відхилено.",
        )
        await callback_query.answer("Заявку відхилено.")
        await callback_query.edit_message_reply_markup(reply_markup=None)

    @staticmethod
    def _parse_callback_data(callback_data: str) -> tuple[str, int]:
        _, action, access_request_id = callback_data.split(":")
        return action, int(access_request_id)
