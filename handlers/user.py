from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import ABOUT_TEXT, ABOUT_US_TEXT, ADMIN_IDS, QUESTIONS_GROUP_CHAT_ID
from database.dao import (
    create_question,
    get_active_faq_items,
    get_faq_item_by_id,
    get_question_by_id,
    record_user,
    set_question_answer,
    set_question_group_message,
)

from handlers.states import AnswerQuestionStates, AskQuestionStates
from keyboards.main import (
    BTN_ABOUT_US,
    BTN_ASK,
    BTN_FAQ,
    CALLBACK_FAQ_ITEM_PREFIX,
    CALLBACK_FAQ_PAGE_PREFIX,
    get_answer_inline_keyboard,
    get_faq_keyboard,
    get_main_keyboard,
)

user_router = Router()
FAQ_PAGE_SIZE = 8


def _user_label(user_id: int, username: str | None) -> str:
    return f"@{username}" if username else f"ID: {user_id}"


@user_router.callback_query(F.data == "noop")
async def noop_callback(callback: CallbackQuery) -> None:
    await callback.answer()


@user_router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext) -> None:
    if not message.from_user:
        return
    await record_user(
        message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
    )
    await state.clear()
    welcome_text = (
        "Привет, студент!\n\n"
        "Этот бот был создан Студенческим советом ВШУ Х ЦТ ИК, чтобы сделать твоё обучение комфортнее. "
        "Здесь ты можешь:\n\n"
        "— задать вопрос по учёбе;\n"
        "— сообщить о поломке в корпусе (сломанная мебель, неработающий свет и др.);\n"
        "— поделиться проблемой, связанной с учебным процессом (некорректное поведение преподавателя, "
        "аттестация, экзамены и др.).\n\n"
        "📌 Просто выбери нужную опцию в меню и напиши свой вопрос, а мы постараемся помочь. "
        "Ответ придёт в течение 2-х дней.\n\n"
        "❗️В случае использования нецензурной лексики, оскорблений, некорректных формулировок или "
        "предоставления ложной информации, сообщение будет заблокировано, и ответа не последует.\n"
    )
    await message.answer(
        welcome_text,
        reply_markup=get_main_keyboard(is_admin=message.from_user.id in ADMIN_IDS),
    )


@user_router.message(Command("about"))
async def cmd_about(message: Message) -> None:
    await message.answer(ABOUT_TEXT)


@user_router.message(Command("get_chat_id"))
async def cmd_get_chat_id(message: Message) -> None:
    await message.answer(
        f"ID этого чата: <code>{message.chat.id}</code>\n"
        f"Тип чата: <code>{message.chat.type}</code>"
    )


@user_router.message(F.text == BTN_ABOUT_US)
async def show_about_us(message: Message) -> None:
    await message.answer(ABOUT_US_TEXT)


@user_router.message(F.text == BTN_FAQ)
async def show_faq_menu(message: Message) -> None:
    faq_items = await get_active_faq_items()
    if not faq_items:
        await message.answer("FAQ пока пуст.")
        return
    pairs = [(item.id, item.question) for item in faq_items]
    await message.answer(
        "Часто задаваемые вопросы:",
        reply_markup=get_faq_keyboard(pairs, page=0, page_size=FAQ_PAGE_SIZE),
    )


@user_router.callback_query(F.data.startswith(CALLBACK_FAQ_PAGE_PREFIX))
async def show_faq_page(callback: CallbackQuery) -> None:
    payload = (callback.data or "").replace(CALLBACK_FAQ_PAGE_PREFIX, "", 1).strip()
    try:
        page = int(payload)
    except ValueError:
        await callback.answer("Некорректная страница", show_alert=True)
        return

    faq_items = await get_active_faq_items()
    pairs = [(item.id, item.question) for item in faq_items]
    await callback.answer()
    await callback.message.edit_reply_markup(
        reply_markup=get_faq_keyboard(pairs, page=page, page_size=FAQ_PAGE_SIZE),
    )


@user_router.callback_query(F.data.startswith(CALLBACK_FAQ_ITEM_PREFIX))
async def show_faq_answer(callback: CallbackQuery) -> None:
    payload = (callback.data or "").replace(CALLBACK_FAQ_ITEM_PREFIX, "", 1).strip()
    try:
        faq_id = int(payload)
    except ValueError:
        await callback.answer("Некорректный FAQ", show_alert=True)
        return

    item = await get_faq_item_by_id(faq_id)
    if not item or not item.is_active:
        await callback.answer("FAQ не найден", show_alert=True)
        return
    await callback.answer()
    await callback.message.answer(f"<b>{item.question}</b>\n\n{item.answer}")


@user_router.message(F.text == BTN_ASK)
async def ask_question_start(message: Message, state: FSMContext) -> None:
    await state.set_state(AskQuestionStates.waiting_question_text)
    await message.answer("Напишите ваш вопрос:")


@user_router.message(AskQuestionStates.waiting_question_text, F.text)
async def ask_question_receive(message: Message, state: FSMContext, bot: Bot) -> None:
    if not message.from_user:
        return
    if not QUESTIONS_GROUP_CHAT_ID:
        await message.answer("Группа для вопросов не настроена.")
        await state.clear()
        return

    text = (message.text or "").strip()
    if not text:
        await message.answer("Вопрос не может быть пустым.")
        return

    await record_user(
        message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
    )
    question = await create_question(
        asker_user_id=message.from_user.id,
        question_text=text,
        asker_username=f"@{message.from_user.username}" if message.from_user.username else None,
    )

    group_text = (
        f"🆕 <b>Вопрос #{question.id}</b>\n"
        f"👤 От: {_user_label(message.from_user.id, message.from_user.username)}\n\n"
        f"{text}"
    )

    try:
        sent = await bot.send_message(
            QUESTIONS_GROUP_CHAT_ID,
            group_text,
            reply_markup=get_answer_inline_keyboard(question.id),
        )
        await set_question_group_message(question.id, QUESTIONS_GROUP_CHAT_ID, sent.message_id)
    except Exception as exc:
        await message.answer(f"Не удалось отправить вопрос в группу: {exc}")
        await state.clear()
        return

    await state.clear()
    await message.answer("Вопрос отправлен. Когда ответят, сообщение придет сюда.")


@user_router.message(AnswerQuestionStates.waiting_answer_text, F.text)
async def collect_question_answer(message: Message, state: FSMContext, bot: Bot) -> None:
    if not message.from_user:
        return
    answer_text = (message.text or "").strip()
    if not answer_text:
        await message.answer("Ответ не может быть пустым.")
        return

    data = await state.get_data()
    question_id = data.get("question_id")
    if not isinstance(question_id, int):
        await state.clear()
        await message.answer("Контекст ответа потерян. Нажмите кнопку в группе еще раз.")
        return

    existing = await get_question_by_id(question_id)
    if not existing or existing.is_answered:
        await state.clear()
        await message.answer("На этот вопрос уже ответили или он недоступен.")
        return

    updated = await set_question_answer(
        question_id,
        answerer_user_id=message.from_user.id,
        answerer_username=f"@{message.from_user.username}" if message.from_user.username else None,
        answer_text=answer_text,
    )
    if not updated:
        await state.clear()
        await message.answer("Не удалось сохранить ответ.")
        return

    group_text = (
        f"✅ <b>Вопрос #{updated.id}</b>\n"
        f"👤 От: {updated.asker_username or updated.asker_user_id}\n\n"
        f"{updated.question_text}\n\n"
        f"💬 <b>Ответил:</b> {updated.answerer_username or updated.answerer_user_id}\n"
        f"{updated.answer_text}"
    )
    try:
        if updated.group_chat_id and updated.group_message_id:
            await bot.edit_message_text(
                chat_id=updated.group_chat_id,
                message_id=updated.group_message_id,
                text=group_text,
            )
    except Exception:
        pass

    try:
        await bot.send_message(
            updated.asker_user_id,
            f"💬 <b>Ответ на ваш вопрос</b>\n\n{updated.answer_text}",
        )
    except Exception:
        await message.answer("Ответ сохранен, но отправить автору не удалось.")

    await state.clear()
    await message.answer("Ответ отправлен автору вопроса.")
