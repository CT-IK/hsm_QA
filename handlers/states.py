from aiogram.fsm.state import State, StatesGroup


class AskQuestionStates(StatesGroup):
    waiting_question_text = State()


class AnswerQuestionStates(StatesGroup):
    waiting_answer_text = State()


class AdminFaqStates(StatesGroup):
    waiting_faq_question = State()
    waiting_faq_answer = State()
    waiting_faq_edit_answer = State()
    waiting_broadcast_text = State()
