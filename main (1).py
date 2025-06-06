
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.enums import ParseMode
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command

API_TOKEN = "7377520849:AAE90iBIivs3iExzl1mm6QxwTt0MYDSG08I"
CHANNEL_ID = -1002567963097  # @GarantBlox
LOG_CHANNEL_ID = -1002664591140  # @GarantBlox_logs

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())

class Feedback(StatesGroup):
    waiting_for_text = State()

@dp.message(Command("start"))
async def cmd_start(message: Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="Оставить отзыв", callback_data="leave_feedback")
    await message.answer("Добро пожаловать! Что вы хотите сделать?", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "leave_feedback")
async def leave_feedback(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Напишите ваш отзыв:")
    await state.set_state(Feedback.waiting_for_text)

@dp.message(Feedback.waiting_for_text)
async def get_feedback(message: Message, state: FSMContext):
    await state.clear()
    feedback_text = message.text
    username = message.from_user.username or message.from_user.full_name
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Одобрить", callback_data=f"approve_{message.from_user.id}")
    builder.button(text="❌ Отклонить", callback_data=f"reject_{message.from_user.id}")
    builder.adjust(2)
    await bot.send_message(
        chat_id=LOG_CHANNEL_ID,
        text=f"📩 Новый отзыв от @{username}:

{feedback_text}",
        reply_markup=builder.as_markup()
    )
    await message.answer("Ваш отзыв отправлен на модерацию. Спасибо!")

@dp.callback_query(F.data.startswith("approve_"))
async def approve_feedback(callback: CallbackQuery):
    user_id = int(callback.data.split("_")[1])
    username = callback.from_user.username or callback.from_user.full_name
    message_text = callback.message.text
    await bot.send_message(CHANNEL_ID, f"📝 Отзыв от @{username}:

{message_text.split('📩 Новый отзыв от ')[-1]}")
    await callback.message.edit_text(f"✅ Отзыв от @{username} одобрен.")
    await callback.answer("Отзыв одобрен.")

@dp.callback_query(F.data.startswith("reject_"))
async def reject_feedback(callback: CallbackQuery):
    username = callback.from_user.username or callback.from_user.full_name
    await callback.message.edit_text(f"❌ Отзыв от @{username} отклонён.")
    await callback.answer("Отзыв отклонён.")

if __name__ == "__main__":
    dp.run_polling(bot)
