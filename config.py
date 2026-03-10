import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ABOUT_TEXT = os.getenv("ABOUT_TEXT", "Information about the department.")


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

    if cards:
        return cards

    return [
        {
            "title": "About department",
            "text": ABOUT_TEXT,
            "photo_url": None,
        },
        {
            "title": "Contacts",
            "text": "Set INFO_CARD_2_TEXT in .env to show contacts.",
            "photo_url": None,
        },
    ]


INFO_CARDS = _build_info_cards()
