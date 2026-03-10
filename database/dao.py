from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .engine import get_session_factory
from .models import FAQItem, Question, User


async def record_user(
    user_id: int,
    *,
    username: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
) -> None:
    async with get_session_factory()() as session:
        await UserDAO(session).upsert(
            user_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
        )


async def get_all_user_ids() -> list[int]:
    async with get_session_factory()() as session:
        return await UserDAO(session).get_all_user_ids()


async def create_question(
    asker_user_id: int,
    question_text: str,
    asker_username: str | None = None,
) -> Question:
    async with get_session_factory()() as session:
        return await QuestionDAO(session).create(
            asker_user_id=asker_user_id,
            question_text=question_text,
            asker_username=asker_username,
        )


async def get_question_by_id(question_id: int) -> Question | None:
    async with get_session_factory()() as session:
        return await QuestionDAO(session).get_by_id(question_id)


async def set_question_group_message(question_id: int, group_chat_id: int, group_message_id: int) -> None:
    async with get_session_factory()() as session:
        await QuestionDAO(session).set_group_message(question_id, group_chat_id, group_message_id)


async def set_question_answer(
    question_id: int,
    answerer_user_id: int,
    answerer_username: str | None,
    answer_text: str,
) -> Question | None:
    async with get_session_factory()() as session:
        return await QuestionDAO(session).set_answer(
            question_id,
            answerer_user_id=answerer_user_id,
            answerer_username=answerer_username,
            answer_text=answer_text,
        )


async def create_faq_item(question: str, answer: str) -> FAQItem:
    async with get_session_factory()() as session:
        return await FAQDAO(session).create(question=question, answer=answer)


async def get_active_faq_items() -> list[FAQItem]:
    async with get_session_factory()() as session:
        return await FAQDAO(session).list_items(active_only=True)


async def get_all_faq_items() -> list[FAQItem]:
    async with get_session_factory()() as session:
        return await FAQDAO(session).list_items(active_only=False)


async def get_faq_item_by_id(item_id: int) -> FAQItem | None:
    async with get_session_factory()() as session:
        return await FAQDAO(session).get_by_id(item_id)


async def update_faq_item(item_id: int, *, question: str | None = None, answer: str | None = None) -> FAQItem | None:
    async with get_session_factory()() as session:
        return await FAQDAO(session).update(item_id=item_id, question=question, answer=answer)


async def delete_faq_item(item_id: int) -> bool:
    async with get_session_factory()() as session:
        return await FAQDAO(session).delete(item_id)


class UserDAO:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert(
        self,
        user_id: int,
        *,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
    ) -> User:
        user = await self.session.get(User, user_id)
        now = datetime.utcnow()
        if user:
            user.username = username or user.username
            user.first_name = first_name or user.first_name
            user.last_name = last_name or user.last_name
            user.last_seen = now
        else:
            user = User(
                user_id=user_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                first_seen=now,
                last_seen=now,
            )
            self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get_all_user_ids(self) -> list[int]:
        result = await self.session.scalars(select(User.user_id))
        return list(result)


class QuestionDAO:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        asker_user_id: int,
        question_text: str,
        asker_username: str | None = None,
    ) -> Question:
        item = Question(
            asker_user_id=asker_user_id,
            asker_username=asker_username,
            question_text=question_text,
        )
        self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def get_by_id(self, question_id: int) -> Question | None:
        return await self.session.get(Question, question_id)

    async def set_group_message(self, question_id: int, group_chat_id: int, group_message_id: int) -> None:
        item = await self.session.get(Question, question_id)
        if not item:
            return
        item.group_chat_id = group_chat_id
        item.group_message_id = group_message_id
        await self.session.commit()

    async def set_answer(
        self,
        question_id: int,
        answerer_user_id: int,
        answerer_username: str | None,
        answer_text: str,
    ) -> Question | None:
        item = await self.session.get(Question, question_id)
        if not item or item.is_answered:
            return None
        item.is_answered = True
        item.answerer_user_id = answerer_user_id
        item.answerer_username = answerer_username
        item.answer_text = answer_text
        item.answered_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(item)
        return item


class FAQDAO:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, question: str, answer: str) -> FAQItem:
        item = FAQItem(question=question, answer=answer, is_active=True)
        self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def list_items(self, active_only: bool) -> list[FAQItem]:
        stmt = select(FAQItem).order_by(FAQItem.id.asc())
        if active_only:
            stmt = stmt.where(FAQItem.is_active.is_(True))
        result = await self.session.scalars(stmt)
        return list(result)

    async def get_by_id(self, item_id: int) -> FAQItem | None:
        return await self.session.get(FAQItem, item_id)

    async def update(self, item_id: int, *, question: str | None = None, answer: str | None = None) -> FAQItem | None:
        item = await self.session.get(FAQItem, item_id)
        if not item:
            return None
        if question is not None:
            item.question = question
        if answer is not None:
            item.answer = answer
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def delete(self, item_id: int) -> bool:
        item = await self.session.get(FAQItem, item_id)
        if not item:
            return False
        await self.session.delete(item)
        await self.session.commit()
        return True
