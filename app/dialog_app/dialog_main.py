from typing import Optional, Dict, Any
from aiogram import types, Bot, exceptions
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot import bot


class QuizBase:
    def __init__(self):
        """
        Initialize a QuizBase instance with empty steps and step data.
        
        Инициализация экземпляра QuizBase с пустыми шагами и данными шагов.
        """
        self.steps = []
        self._step_data = {}

    def add_step(self, text: str, data_key: str, keyboard: Optional[InlineKeyboardMarkup] = None):
        """
        Add a step to the quiz.
        
        Добавить шаг в опрос.
        
        Args:
            text (str): The text to display for the step.
            data_key (str): The key to store the user's answer for this step.
            keyboard (Optional[InlineKeyboardMarkup]): Optional keyboard markup for the step.
        
        Returns:
            self: Enables method chaining.
        """
        self.steps.append({
            "text": text,
            "data_key": data_key,
            "keyboard": keyboard,
        })
        return self

    def end_quiz(self, confirmation_text: str = "Подтвердите добавление"):
        """
        Add a confirmation step to the quiz for final approval or cancellation.
        
        Добавить шаг подтверждения в опрос для окончательного подтверждения или отмены.
        
        Args:
            confirmation_text (str): The text to display for confirmation.
        
        Returns:
            self: Enables method chaining.
        """
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
        """
        Start the quiz by sending the first step to the user.
        
        Начать опрос, отправив первый шаг пользователю.
        
        Args:
            message (types.Message): The message object to reply to.
        """
        await self._send_step(message, 0)

    async def _send_step(
            self,
            message_or_callback: types.Message | types.CallbackQuery,
            step_index: int):
        """
        Send a specific step to the user.
        
        Отправить конкретный шаг пользователю.
        
        Args:
            message_or_callback: The message or callback to reply to.
            step_index (int): The index of the step to send.
        """
        step = self.steps[step_index]
        if step["keyboard"]:
            bot_message = await message_or_callback.answer(step["text"], reply_markup=step["keyboard"])
        else:
            bot_message = await message_or_callback.answer(step["text"])
        return bot_message

    def get_step(self, step_index: int) -> Dict[str, Any]:
        """
        Get the step dictionary by index.
        
        Получить словарь шага по индексу.
        
        Args:
            step_index (int): The index of the step.
        
        Returns:
            Dict[str, Any]: The step data.
        """
        return self.steps[step_index]

    def total_steps(self) -> int:
        """
        Get the total number of steps in the quiz.
        
        Получить общее количество шагов в опросе.
        
        Returns:
            int: The number of steps.
        """
        return len(self.steps)

    async def delete_prev_messages(
            self, instance: types.Message | types.CallbackQuery,
            trash_messages_ids: list,
            delete_messages: bool
    ):
        """
        Delete previous messages from the user.

        Удалить предыдущие сообщения от пользователя.

        Args:
            instance (types.Message | types.CallbackQuery): The incoming message or callback query.
            trash_messages_ids (list): The list of message IDs to delete.
            delete_messages (bool): Whether to delete messages or not.
        """
        if not delete_messages:
            return

        if isinstance(instance, types.Message):
            message = instance
        elif isinstance(instance, types.CallbackQuery):
            message = instance.message
        else:
            raise ValueError("instance must be types.Message or types.CallbackQuery")

        if trash_messages_ids:
            await bot.delete_messages(
                chat_id=message.chat.id,
                message_ids=trash_messages_ids)

class QuizHandler(QuizBase):
    def __init__(self, delete_used_messages: bool = True):
        super().__init__()
        self.delete_used_messages = delete_used_messages

    async def process_step(
            self,
            instance: types.Message | types.CallbackQuery,
            state: FSMContext,
    ):
        """
        Process a step from the user during the quiz flow.

        Обработать шаг от пользователя во время прохождения опроса.

        Args:
            instance (types.Message | types.CallbackQuery): The incoming message or callback query.
            state (FSMContext): The FSM context for storing quiz state.
        :return: The collected state data from the quiz.
        """

        state_data = await state.get_data()

        trash_messages_ids = (
            [] if state_data.get("trash_messages_ids") is None
            else state_data.get("trash_messages_ids")
        )

        if isinstance(instance, types.Message):
            bot_answer = await self.process_message(instance, state)
            await self.delete_prev_messages(
                bot_answer,
                trash_messages_ids,
                self.delete_used_messages,
            )
            trash_messages_ids.append(bot_answer.message_id)

        elif isinstance(instance, types.CallbackQuery):
            if self.delete_used_messages:
                await instance.message.delete()
            bot_answer = await self.process_callback(instance, state)
            if isinstance(bot_answer, dict):
                return bot_answer

            await self.delete_prev_messages(
                bot_answer,
                trash_messages_ids,
                self.delete_used_messages
            )
            trash_messages_ids.append(bot_answer.message_id)

        else:
            raise TypeError(f"Unsupported instance type: {type(instance)}")

        await state.update_data(trash_messages_ids=trash_messages_ids)

    async def process_message(self, message: types.Message, state: FSMContext):
        """
        Process a message from the user during the quiz flow.
        
        Обработать сообщение от пользователя во время прохождения опроса.
        
        Args:
            message (types.Message): The incoming message.
            state (FSMContext): The FSM context for storing quiz state.
        """
        state_data = await state.get_data()

        step_index = state_data.get("step", 1)
        if step_index > 0:
            prev_step = self.get_step(step_index - 1)
            await state.update_data(**{prev_step["data_key"]: message.text})
        if step_index < self.total_steps():
            bot_answer = await self._send_step(message, step_index)
            await state.update_data(step=step_index + 1)
            return bot_answer

    async def process_callback(self, callback_query: types.CallbackQuery, state: FSMContext):
        """
        Process a callback query from the user (e.g., button presses) during the quiz flow.
        
        Обработать callback-запрос от пользователя (например, нажатия кнопок) во время прохождения опроса.
        
        Args:
            callback_query (types.CallbackQuery): The callback query object.
            state (FSMContext): The FSM context for storing quiz state.
        """
        state_data = await state.get_data()
        step_index = state_data.get("step", 1)
        try:
            await callback_query.message.delete_reply_markup()
        except exceptions.TelegramBadRequest:
            pass
        if callback_query.data in ("approve", "cancel"):
            collected_data = await self.process_quiz_end(callback_query, state, state_data)
            return collected_data
        if step_index > 0:
            prev_step = self.get_step(step_index - 1)
            await state.update_data(**{prev_step["data_key"]: callback_query.data})
        if step_index < self.total_steps():
            bot_answer = await self._send_step(callback_query.message, step_index)
            await state.update_data(step=step_index + 1)
            return bot_answer

    async def process_quiz_end(
            self, callback_query: types.CallbackQuery,
            state: FSMContext,
            state_data: dict
    ):
        """
        Handle the end of the quiz, processing approval or cancellation.
        
        Обработать окончание опроса, обработав подтверждение или отмену.
        
        Args:
            callback_query (types.CallbackQuery): The callback query object.
            state (FSMContext): The FSM context for storing quiz state.
            state_data (dict): The collected state data from the quiz.
        """
        if callback_query.data == "approve":
            await callback_query.message.answer("Добавление завершено")
        else:
            await callback_query.message.answer("Добавление отменено")
        await state.clear()
        return state_data
