from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_seen: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_seen: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    asker_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    asker_username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)

    group_chat_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    group_message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    is_answered: Mapped[bool] = mapped_column(Boolean, default=False)
    answerer_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    answerer_username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    answer_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    answered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class FAQItem(Base):
    __tablename__ = "faq_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    question: Mapped[str] = mapped_column(String(500), nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
