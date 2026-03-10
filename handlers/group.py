from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import CallbackQuery

from database.dao import get_question_by_id, record_user
from handlers.states import AnswerQuestionStates
from keyboards.main import CALLBACK_ANSWER_PREFIX

group_router = Router()


@group_router.callback_query(F.data.startswith(CALLBACK_ANSWER_PREFIX))
async def answer_question_callback(
    callback: CallbackQuery,
    bot: Bot,
    dispatcher: Dispatcher,
) -> None:
    if not callback.from_user:
        return

    payload = (callback.data or "").replace(CALLBACK_ANSWER_PREFIX, "", 1).strip()
    try:
        question_id = int(payload)
    except ValueError:
        await callback.answer("Invalid payload.", show_alert=True)
        return

    question = await get_question_by_id(question_id)
    if not question:
        await callback.answer("Question not found.", show_alert=True)
        return
    if question.is_answered:
        await callback.answer("This question already has an answer.", show_alert=True)
        return

    await record_user(
        callback.from_user.id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name,
        last_name=callback.from_user.last_name,
    )

    state = dispatcher.fsm.get_context(
        bot=bot,
        chat_id=callback.from_user.id,
        user_id=callback.from_user.id,
    )
    await state.set_state(AnswerQuestionStates.waiting_answer_text)
    await state.update_data(question_id=question_id)

    try:
        await bot.send_message(
            callback.from_user.id,
            f"Вы выбрали вопрос #{question.id}. Напишите ответ в этом чате:\n\n{question.question_text}",
        )
        await callback.answer("Проверьте личные сообщения с ботом.")
    except Exception:
        await state.clear()
        await callback.answer(
            "Сначала откройте личный чат с ботом и нажмите /start.",
            show_alert=True,
        )
