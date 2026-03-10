from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

BTN_ASK = "❓ Задать вопрос"
BTN_INFO = "ℹ️ Информация"
BTN_FAQ = "📚 FAQ"
BTN_ADMIN = "🛠 Админ-панель"

CALLBACK_ANSWER_PREFIX = "ans_"
CALLBACK_INFO_ITEM_PREFIX = "info_item_"
CALLBACK_INFO_PAGE_PREFIX = "info_page_"
CALLBACK_FAQ_ITEM_PREFIX = "faq_item_"
CALLBACK_FAQ_PAGE_PREFIX = "faq_page_"

CALLBACK_ADMIN_ADD_FAQ = "adm_faq_add"
CALLBACK_ADMIN_LIST_FAQ = "adm_faq_list"
CALLBACK_ADMIN_EDIT_FAQ = "adm_faq_edit"
CALLBACK_ADMIN_EDIT_FAQ_PREFIX = "adm_faq_edit_"
CALLBACK_ADMIN_DELETE_FAQ = "adm_faq_delete"
CALLBACK_ADMIN_DELETE_FAQ_PREFIX = "adm_faq_del_"
CALLBACK_ADMIN_BROADCAST = "adm_broadcast"


def get_main_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text=BTN_ASK)],
        [KeyboardButton(text=BTN_INFO), KeyboardButton(text=BTN_FAQ)],
    ]
    if is_admin:
        rows.append([KeyboardButton(text=BTN_ADMIN)])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def get_answer_inline_keyboard(question_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Ответить на вопрос", callback_data=f"{CALLBACK_ANSWER_PREFIX}{question_id}")]
        ]
    )


def _build_pagination_row(prefix: str, page: int, total_pages: int) -> list[InlineKeyboardButton]:
    row: list[InlineKeyboardButton] = []
    if page > 0:
        row.append(InlineKeyboardButton(text="⬅️", callback_data=f"{prefix}{page - 1}"))
    row.append(InlineKeyboardButton(text=f"{page + 1}/{total_pages}", callback_data="noop"))
    if page < total_pages - 1:
        row.append(InlineKeyboardButton(text="➡️", callback_data=f"{prefix}{page + 1}"))
    return row


def get_info_cards_keyboard(cards: list[dict[str, str | None]], page: int = 0, page_size: int = 5) -> InlineKeyboardMarkup:
    total_pages = max(1, (len(cards) + page_size - 1) // page_size)
    page = max(0, min(page, total_pages - 1))
    start = page * page_size
    end = start + page_size

    buttons = []
    for idx, card in enumerate(cards[start:end], start=start):
        title = card["title"] or f"Карточка {idx + 1}"
        buttons.append([InlineKeyboardButton(text=title, callback_data=f"{CALLBACK_INFO_ITEM_PREFIX}{idx}")])

    if total_pages > 1:
        buttons.append(_build_pagination_row(CALLBACK_INFO_PAGE_PREFIX, page, total_pages))

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_faq_keyboard(faq_items: list[tuple[int, str]], page: int = 0, page_size: int = 8) -> InlineKeyboardMarkup:
    total_pages = max(1, (len(faq_items) + page_size - 1) // page_size)
    page = max(0, min(page, total_pages - 1))
    start = page * page_size
    end = start + page_size

    buttons = []
    for item_id, title in faq_items[start:end]:
        buttons.append([InlineKeyboardButton(text=title[:80], callback_data=f"{CALLBACK_FAQ_ITEM_PREFIX}{item_id}")])

    if total_pages > 1:
        buttons.append(_build_pagination_row(CALLBACK_FAQ_PAGE_PREFIX, page, total_pages))

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_admin_panel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить FAQ", callback_data=CALLBACK_ADMIN_ADD_FAQ)],
            [InlineKeyboardButton(text="📋 Список FAQ", callback_data=CALLBACK_ADMIN_LIST_FAQ)],
            [InlineKeyboardButton(text="✏️ Редактировать FAQ", callback_data=CALLBACK_ADMIN_EDIT_FAQ)],
            [InlineKeyboardButton(text="🗑 Удалить FAQ", callback_data=CALLBACK_ADMIN_DELETE_FAQ)],
            [InlineKeyboardButton(text="📣 Рассылка", callback_data=CALLBACK_ADMIN_BROADCAST)],
        ]
    )


def get_admin_delete_faq_keyboard(faq_items: list[tuple[int, str]], for_edit: bool = False) -> InlineKeyboardMarkup:
    buttons = []
    for item_id, title in faq_items:
        if for_edit:
            text = f"Изменить #{item_id}: {title[:36]}"
            data = f"{CALLBACK_ADMIN_EDIT_FAQ_PREFIX}{item_id}"
        else:
            text = f"Удалить #{item_id}: {title[:36]}"
            data = f"{CALLBACK_ADMIN_DELETE_FAQ_PREFIX}{item_id}"
        buttons.append(
            [
                InlineKeyboardButton(
                    text=text,
                    callback_data=data,
                )
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=buttons)
