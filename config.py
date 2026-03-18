import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ABOUT_TEXT = os.getenv("ABOUT_TEXT", "Information about the department.")

# Текст для кнопки «О нас» (с гиперссылками)
ABOUT_US_TEXT = (
    "Привет, студент!\n\n"
    "Твои проблемы очень важны, и мы работаем, чтобы их решать. "
    "По всем срочным и сложным вопросам ты всегда можешь написать напрямую нам:\n\n"
    "Председатель Студенческого совета факультета ВШУ — @anratnikovaa\n"
    "Заместитель Председателя по учебно-социальной деятельности — @pollillixs\n\n"
    "Подписывайся на наши медиа, чтобы быть в курсе всех событий:\n"
    '<a href="https://vk.com/hsmedia">HSMedia</a>\n'
    '<a href="https://vk.com/hsmedia">Студенческий совет ВШУ | Финансовый университет</a>\n'
    '<a href=" https://vk.com/hsmedia">ВШУм</a>'
)


def _parse_int(value: str | None) -> int | None:
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _parse_admin_ids(value: str | None) -> set[int]:
    if not value:
        return set()
    result: set[int] = set()
    for part in value.split(","):
        parsed = _parse_int(part.strip())
        if parsed is not None:
            result.add(parsed)
    return result


QUESTIONS_GROUP_CHAT_ID = _parse_int(os.getenv("QUESTIONS_GROUP_CHAT_ID"))
ADMIN_IDS = _parse_admin_ids(os.getenv("ADMIN_IDS"))


def _build_info_cards() -> list[dict[str, str | None]]:
    """Карточки для раздела «О нас» (если заданы в .env). Иначе используется только ABOUT_US_TEXT."""
    cards: list[dict[str, str | None]] = []
    for idx in range(1, 5):
        title = (os.getenv(f"INFO_CARD_{idx}_TITLE") or "").strip()
        text = (os.getenv(f"INFO_CARD_{idx}_TEXT") or "").strip()
        photo_url = (os.getenv(f"INFO_CARD_{idx}_PHOTO_URL") or "").strip()
        if title and text:
            cards.append(
                {
                    "title": title,
                    "text": text,
                    "photo_url": photo_url or None,
                }
            )
    return cards


INFO_CARDS = _build_info_cards()
