from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import ADMIN_IDS
from database.dao import (
    create_faq_item,
    delete_faq_item,
    get_all_faq_items,
    get_all_user_ids,
    record_user,
    update_faq_item,
)
from handlers.states import AdminFaqStates
from keyboards.main import (
    BTN_ADMIN,
    CALLBACK_ADMIN_ADD_FAQ,
    CALLBACK_ADMIN_BROADCAST,
    CALLBACK_ADMIN_DELETE_FAQ,
    CALLBACK_ADMIN_DELETE_FAQ_PREFIX,
    CALLBACK_ADMIN_EDIT_FAQ,
    CALLBACK_ADMIN_EDIT_FAQ_PREFIX,
    CALLBACK_ADMIN_LIST_FAQ,
    get_admin_delete_faq_keyboard,
    get_admin_panel_keyboard,
)

admin_router = Router()


def _is_admin(user_id: int | None) -> bool:
    return bool(user_id and user_id in ADMIN_IDS)


async def _show_panel(message: Message) -> None:
    await message.answer("Панель администратора:", reply_markup=get_admin_panel_keyboard())


@admin_router.message(Command("admin"))
@admin_router.message(F.text == BTN_ADMIN)
async def open_admin_panel(message: Message) -> None:
    user_id = message.from_user.id if message.from_user else None
    if not _is_admin(user_id):
        return
    if message.from_user:
        await record_user(
            message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
        )
    await _show_panel(message)


@admin_router.callback_query(F.data == CALLBACK_ADMIN_ADD_FAQ)
async def admin_add_faq_start(callback: CallbackQuery, state: FSMContext) -> None:
    if not _is_admin(callback.from_user.id if callback.from_user else None):
        return
    await state.set_state(AdminFaqStates.waiting_faq_question)
    await callback.answer()
    await callback.message.answer("Отправьте вопрос для FAQ:")


@admin_router.message(AdminFaqStates.waiting_faq_question, F.text)
async def admin_add_faq_question(message: Message, state: FSMContext) -> None:
    if not _is_admin(message.from_user.id if message.from_user else None):
        return
    question = (message.text or "").strip()
    if not question:
        await message.answer("Вопрос не может быть пустым.")
        return
    await state.update_data(faq_question=question)
    await state.set_state(AdminFaqStates.waiting_faq_answer)
    await message.answer("Теперь отправьте ответ для FAQ:")


@admin_router.message(AdminFaqStates.waiting_faq_answer, F.text)
async def admin_add_faq_answer(message: Message, state: FSMContext) -> None:
    if not _is_admin(message.from_user.id if message.from_user else None):
        return
    answer = (message.text or "").strip()
    if not answer:
        await message.answer("Ответ не может быть пустым.")
        return

    data = await state.get_data()
    question = data.get("faq_question")
    if not isinstance(question, str) or not question:
        await state.clear()
        await message.answer("Состояние потеряно. Начните заново из админ-панели.")
        return

    item = await create_faq_item(question=question, answer=answer)
    await state.clear()
    await message.answer(f"FAQ #{item.id} создан.")
    await _show_panel(message)


@admin_router.callback_query(F.data == CALLBACK_ADMIN_LIST_FAQ)
async def admin_list_faq(callback: CallbackQuery) -> None:
    if not _is_admin(callback.from_user.id if callback.from_user else None):
        return
    items = await get_all_faq_items()
    await callback.answer()
    if not items:
        await callback.message.answer("FAQ пуст.")
        return

    lines = ["Список FAQ:"]
    for item in items:
        lines.append(f"#{item.id} - {item.question}")
    await callback.message.answer("\n".join(lines[:120]))


@admin_router.callback_query(F.data == CALLBACK_ADMIN_EDIT_FAQ)
async def admin_edit_faq_menu(callback: CallbackQuery) -> None:
    if not _is_admin(callback.from_user.id if callback.from_user else None):
        return
    items = await get_all_faq_items()
    await callback.answer()
    if not items:
        await callback.message.answer("FAQ пуст, редактировать нечего.")
        return
    pairs = [(item.id, item.question) for item in items[:40]]
    await callback.message.answer(
        "Выберите FAQ для изменения ответа:",
        reply_markup=get_admin_delete_faq_keyboard(pairs, for_edit=True),
    )


@admin_router.callback_query(F.data.startswith(CALLBACK_ADMIN_EDIT_FAQ_PREFIX))
async def admin_edit_faq_start(callback: CallbackQuery, state: FSMContext) -> None:
    if not _is_admin(callback.from_user.id if callback.from_user else None):
        return
    payload = (callback.data or "").replace(CALLBACK_ADMIN_EDIT_FAQ_PREFIX, "", 1).strip()
    try:
        item_id = int(payload)
    except ValueError:
        await callback.answer("Некорректный ID FAQ", show_alert=True)
        return
    await state.set_state(AdminFaqStates.waiting_faq_edit_answer)
    await state.update_data(faq_edit_id=item_id)
    await callback.answer()
    await callback.message.answer("Отправьте новый ответ для выбранного FAQ:")


@admin_router.message(AdminFaqStates.waiting_faq_edit_answer, F.text)
async def admin_edit_faq_answer(message: Message, state: FSMContext) -> None:
    if not _is_admin(message.from_user.id if message.from_user else None):
        return
    answer = (message.text or "").strip()
    if not answer:
        await message.answer("Ответ не может быть пустым.")
        return
    data = await state.get_data()
    item_id = data.get("faq_edit_id")
    if not isinstance(item_id, int):
        await state.clear()
        await message.answer("Состояние потеряно. Начните заново.")
        return
    updated = await update_faq_item(item_id, answer=answer)
    await state.clear()
    if not updated:
        await message.answer("FAQ не найден.")
        return
    await message.answer(f"FAQ #{updated.id} обновлён.")
    await _show_panel(message)


@admin_router.callback_query(F.data == CALLBACK_ADMIN_DELETE_FAQ)
async def admin_delete_faq_menu(callback: CallbackQuery) -> None:
    if not _is_admin(callback.from_user.id if callback.from_user else None):
        return

    items = await get_all_faq_items()
    await callback.answer()
    if not items:
        await callback.message.answer("Удалять нечего.")
        return
    pairs = [(item.id, item.question) for item in items[:40]]
    await callback.message.answer(
        "Выберите FAQ для удаления:",
        reply_markup=get_admin_delete_faq_keyboard(pairs),
    )


@admin_router.callback_query(F.data.startswith(CALLBACK_ADMIN_DELETE_FAQ_PREFIX))
async def admin_delete_faq_item(callback: CallbackQuery) -> None:
    if not _is_admin(callback.from_user.id if callback.from_user else None):
        return
    payload = (callback.data or "").replace(CALLBACK_ADMIN_DELETE_FAQ_PREFIX, "", 1).strip()
    try:
        item_id = int(payload)
    except ValueError:
        await callback.answer("Некорректный ID FAQ", show_alert=True)
        return

    deleted = await delete_faq_item(item_id)
    await callback.answer()
    if deleted:
        await callback.message.answer(f"FAQ #{item_id} удалён.")
    else:
        await callback.message.answer("FAQ не найден.")


@admin_router.callback_query(F.data == CALLBACK_ADMIN_BROADCAST)
async def admin_broadcast_start(callback: CallbackQuery, state: FSMContext) -> None:
    if not _is_admin(callback.from_user.id if callback.from_user else None):
        return
    await state.set_state(AdminFaqStates.waiting_broadcast_text)
    await callback.answer()
    await callback.message.answer("Отправьте текст рассылки одним сообщением:")


@admin_router.message(AdminFaqStates.waiting_broadcast_text, F.text)
async def admin_broadcast_send(message: Message, state: FSMContext) -> None:
    if not _is_admin(message.from_user.id if message.from_user else None):
        return
    text = (message.text or "").strip()
    if not text:
        await message.answer("Текст рассылки не может быть пустым.")
        return

    bot = message.bot
    user_ids = await get_all_user_ids()
    ok_count = 0
    fail_count = 0

    for user_id in user_ids:
        try:
            await bot.send_message(user_id, text)
            ok_count += 1
        except Exception:
            fail_count += 1

    await state.clear()
    await message.answer(
        f"Рассылка завершена.\nУспешно: {ok_count}\nОшибок: {fail_count}"
    )
    await _show_panel(message)
