import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import web
from aiogram import Router

# === НАСТРОЙКИ ===
TOKEN = "7377520849:AAE90iBIivs3iExzl1mm6QxwTt0MYDSG08I"  # ❗ Замените на переменную окружения позже
CHANNEL_ID = -1002567963097       # Основной канал @GarantBlox
LOG_CHANNEL_ID = -1002664591140   # Лог-канал @GarantBlox_logs
ADMIN_ID = 1725224593             # Telegram user_id гаранта

# === ИНИЦИАЛИЗАЦИЯ ===
bot = Bot(token=TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

# === ВРЕМЕННОЕ ХРАНЕНИЕ ===
orders = {}
feedbacks = {}

# === ВЕБ-ХЕНДЛЕР (для Render или UptimeRobot) ===
async def handle(request):
    return web.Response(text="OK")

# === СТАРТ-КОМАНДА ===
@router.message(Command("start"))
async def start_handler(message: Message):
    kb = ReplyKeyboardBuilder()
    kb.add(types.KeyboardButton(text="🛒 Оформить заказ"))
    kb.add(types.KeyboardButton(text="💬 Оставить отзыв"))
    await message.answer(
        "Добро пожаловать! Выберите действие:",
        reply_markup=kb.as_markup(resize_keyboard=True)
    )

# === ОБРАБОТКА ЗАКАЗА ===
@router.message(F.text == "🛒 Оформить заказ")
async def order_handler(message: Message):
    await message.answer("Пожалуйста, напишите детали заказа:")
    orders[message.from_user.id] = {"stage": "waiting_for_details"}

# === ПОЛУЧЕНИЕ ДЕТАЛЕЙ ЗАКАЗА ===
@router.message(lambda msg: msg.from_user.id in orders and orders[msg.from_user.id]["stage"] == "waiting_for_details")
async def order_details_handler(message: Message):
    order_text = message.text
    orders.pop(message.from_user.id)

    await bot.send_message(
        LOG_CHANNEL_ID,
        f"🆕 Новый заказ от @{message.from_user.username or 'без username'}:\n\n{order_text}"
    )

    await message.answer("Ваш заказ принят! Ожидайте ответа гаранта.")

# === ОБРАБОТКА ОТЗЫВА ===
@router.message(F.text == "💬 Оставить отзыв")
async def feedback_handler(message: Message):
    await message.answer("Пожалуйста, отправьте ваш отзыв:")
    feedbacks[message.from_user.id] = True

# === ПОЛУЧЕНИЕ ОТЗЫВА ===
@router.message(lambda msg: msg.from_user.id in feedbacks)
async def save_feedback_handler(message: Message):
    feedback_text = message.text
    feedbacks.pop(message.from_user.id)

    await bot.send_message(
        LOG_CHANNEL_ID,
        f"🌟 Новый отзыв от @{message.from_user.username or 'без username'}:\n\n{feedback_text}"
    )

    await message.answer("Спасибо за ваш отзыв!")

# === ЗАПУСК БОТА ===
async def main():
    app = web.Application()
    app.router.add_get("/", handle)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, port=8080)
    await site.start()

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
