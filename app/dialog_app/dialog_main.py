from typing import Optional, Dict, Any
from aiogram import types, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


class QuizBase:
    def __init__(self):
        self.steps = []
        self._step_data = {}

    def add_step(self, text: str, data_key: str, keyboard: Optional[InlineKeyboardMarkup] = None):
        self.steps.append({
            "text": text,
            "data_key": data_key,
            "keyboard": keyboard,
        })
        return self

    def end_quiz(self, confirmation_text: str = "Подтвердите добавление"):
        self.steps.append({
            "text": confirmation_text,
            "data_key": "quest_confirmation",
            "keyboard": InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="Добавить", callback_data="approve")],
                    [InlineKeyboardButton(text="Отменить", callback_data="cancel")]
                ]
            )
        })
        return self

    async def start(self, message: types.Message):
        await self._send_step(message, 0)

    async def _send_step(self, message_or_callback, step_index: int):
        step = self.steps[step_index]
        if step["keyboard"]:
            await message_or_callback.answer(step["text"], reply_markup=step["keyboard"])
        else:
            await message_or_callback.answer(step["text"])

    def get_step(self, step_index: int) -> Dict[str, Any]:
        return self.steps[step_index]

    def total_steps(self) -> int:
        return len(self.steps)

class QuizHandler(QuizBase):
    async def process_message(self, message: types.Message, state: FSMContext):
        state_data = await state.get_data()
        step_index = state_data.get("step", 1)
        if step_index > 0:
            prev_step = self.get_step(step_index - 1)
            await state.update_data(**{prev_step["data_key"]: message.text})
        if step_index < self.total_steps():
            await self._send_step(message, step_index)
            await state.update_data(step=step_index + 1)

    async def process_callback(self, callback_query: types.CallbackQuery, state: FSMContext):
        state_data = await state.get_data()
        step_index = state_data.get("step", 1)
        if callback_query.data in ("approve", "cancel"):
            await self.process_quiz_end(callback_query, state, state_data)
            return
        if step_index > 0:
            prev_step = self.get_step(step_index - 1)
            await state.update_data(**{prev_step["data_key"]: callback_query.data})
        if step_index < self.total_steps():
            await self._send_step(callback_query.message, step_index)
            await state.update_data(step=step_index + 1)

    async def process_quiz_end(self, callback_query: types.CallbackQuery, state: FSMContext, state_data: dict):
        if callback_query.data == "approve":
            await callback_query.message.answer(f"Собранные данные: {state_data}")
        else:
            await callback_query.message.answer("Добавление квеста отменено")
        await state.clear()
