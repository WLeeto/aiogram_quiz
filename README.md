# Описание

Этот проект содержит пример класса для упрощения создания опросников (quiz/questionnaire) через библиотеку aiogram. Класс позволяет быстро собирать пошаговые опросы с поддержкой inline-клавиатур и автоматическим сохранением ответов пользователей через FSM.

Подходит для интеграции в Telegram-ботов на aiogram 3.x.

## Использование
```python
import logging

from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from app.dialog_app.dialog_main import QuizHandler

router = Router()


logger = logging.getLogger(__name__)


class TestAddQuestStates(StatesGroup):
    start = State()


new_quiz = QuizHandler()
new_quiz.add_step(text="Первый шаг c клавиатурой", data_key="step_1", keyboard=InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Кнопка 1", callback_data="button_1"),
            InlineKeyboardButton(text="Кнопка 2", callback_data="button_2"),
        ],
    ]
))
new_quiz.add_step(text="Второй шаг без клавиатуры", data_key="step_2")
new_quiz.add_step(text="Третий шаг с клавиатурой", data_key="step_3", keyboard=InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Кнопка 1", callback_data="button_1"),
            InlineKeyboardButton(text="Кнопка 2", callback_data="button_2"),
        ],
        [
            InlineKeyboardButton(text="Кнопка 3", callback_data="button_3"),
            InlineKeyboardButton(text="Кнопка 4", callback_data="button_4"),
        ],
    ]
))
new_quiz.add_step(text="Четвертый шаг без клавиатуры", data_key="step_4")
new_quiz.end_quiz()


@router.message(F.text == "/test")
async def test_command(message: types.Message, state: FSMContext):
    await state.set_state(TestAddQuestStates.start)
    await new_quiz.start(message)


@router.message(TestAddQuestStates.start)
async def start_test_q(message: types.Message, state: FSMContext):
    await new_quiz.process_message(message, state)


@router.callback_query(TestAddQuestStates.start)
async def process_query_answer(callback_query: types.CallbackQuery, state: FSMContext):
    collected_data = await new_quiz.process_callback(callback_query, state)
    print(collected_data)
```

## Доработки
- Поддержка удаления старых сообщений