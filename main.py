import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import web
from aiogram import Router

TOKEN = "7377520849:AAE90iBIivs3iExzl1mm6QxwTt0MYDSG08I"
CHANNEL_ID = '@GarantBlox'
LOG_CHANNEL_ID = '@GarantBlox_logs'
ADMIN_ID = 1725224593  # Telegram user_id гаранта

bot = Bot(token=TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

orders = {}   # Хранение заказов
feedbacks = {}  # Хранение отзывов

# Веб-хендлер проверки статуса
async def handle(request):
    return web.Response(text="I'm alive!")

app = web.Application()
app.add_routes([web.get("/", handle)])

@router.message(Command("start"))
async def start(message: Message):
    keyboard = ReplyKeyboardBuilder()
    keyboard.add(types.KeyboardButton(text="📝 Оставить отзыв"))
    keyboard.add(types.KeyboardButton(text="📦 Сделать заказ гаранту"))
    await message.answer(
        "Привет! 👋
