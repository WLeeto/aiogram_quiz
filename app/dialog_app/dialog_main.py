import asyncio

from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


class BaseQuiz:

    def __init__(self):
        self.structure = {
            0: "",
        }

    async def start(self, message: types.Message):
        text = self.structure[1]["text"]
        if self.structure[1].get("keyboard"):
            keyboard = self.structure[1]["keyboard"]
            await message.answer(text, reply_markup=keyboard)
        else:
            await message.answer(text)


    def add_step(self, text: str, data_key: str, keyboard: InlineKeyboardMarkup=None):
        """
        Add new step to quiz.
        :param text: Question text.
        :param data_key: Text as data - key wich will be saved in quiz data.
        :param keyboard: InlineKeyboardMarkup if question assume to have keyboard.
        :return:
        """
        new_step_value = {len(self.structure): {
            "text": text,
            "data_key": data_key,
            "keyboard": keyboard,}
        }
        self.structure.update(new_step_value)

    def end_quiz(self, confirmation_text: str = "Подтвердите добавление"):
        end_quiz_step = {len(self.structure): {
            "text": confirmation_text,
            "data_key": "quest_confirmation",
            "keyboard": InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="Добавить", callback_data="approve")],
                    [InlineKeyboardButton(text="Отменить", callback_data="cancel")]
                ]
            )
        }}
        self.structure.update(end_quiz_step)


class QuizMessageHandler(BaseQuiz):
    def __init__(self):
        super().__init__()

    async def process_message(
            self, message: types.Message,
            state: FSMContext
    ):
        state_data = await state.get_data()
        current_step = state_data.get("step")
        if not current_step:
            current_step = 2

        if self.structure[current_step - 1].get("keyboard"):
            answer = await message.answer("Выберите одну из кнопок")
            await asyncio.sleep(3)
            await answer.delete()
            return

        if current_step != 1:
            key = self.structure[current_step - 1]["data_key"]
            value = message.text

            await state.update_data(**{key: value})

        if self.structure[current_step].get("keyboard"):
            await message.answer(
                self.structure[current_step]["text"],
                reply_markup=self.structure[current_step]["keyboard"]
            )
        else:
            await message.answer(self.structure[current_step]["text"])

        current_step += 1
        await state.update_data(step=current_step)


class QuizCallbackHandler(BaseQuiz):
    def __init__(self):
        super().__init__()

    async def process_callback(
            self,
            callback_query: types.CallbackQuery,
            state: FSMContext
    ):
        state_data = await state.get_data()
        current_step = state_data.get("step")
        if not current_step:
            current_step = 2

        end = await self.process_quiz_end(callback_query, state, state_data)
        if end:
            return

        if current_step != 1:
            key = self.structure[current_step - 1]["data_key"]
            value = callback_query.data

            await state.update_data(**{key: value})

        if self.structure[current_step].get("keyboard"):
            await callback_query.message.answer(
                self.structure[current_step]["text"],
                reply_markup=self.structure[current_step]["keyboard"])
        else:
            await callback_query.message.answer(self.structure[current_step]["text"])

        current_step += 1
        await state.update_data(step=current_step)


    async def process_quiz_end(
            self, callback_query: types.CallbackQuery,
            state: FSMContext,
            state_data: dict,
            confirm_message_text: str = None,
            decline_message_text: str = None
    ):
        if callback_query.data == "approve":
            if not confirm_message_text:
                confirm_message_text = f"Собранные данные: {state_data}"
            await callback_query.message.answer(confirm_message_text)
            await state.clear()
            return True
        elif callback_query.data == "cancel":
            if not decline_message_text:
                decline_message_text = "Добавление квеста отменено"
            await callback_query.message.answer(decline_message_text)
            await state.clear()
            return True

class QuizQueryHandler(QuizMessageHandler, QuizCallbackHandler):
    ...
