import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiohttp import web

from aiogram import Router

TOKEN = "7377520849:AAFKMxzbjJfQfSc-SWI0QAFG7JzYWcax8bQ"
CHANNEL_ID = '@GarantBlox'

bot = Bot(token=TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

# Веб-хендлер для проверки, что сервер живой
async def handle(request):
    return web.Response(text="I'm alive!")

app = web.Application()
app.add_routes([web.get("/", handle)])

@router.message(Command("start"))
async def start(message: Message):
    keyboard = ReplyKeyboardBuilder()
    keyboard.add(types.KeyboardButton(text="📝 Оставить отзыв"))
    await message.answer(
        "Привет! 👋 Здесь ты можешь оставить отзыв о работе гаранта GarantBlox.",
        reply_markup=keyboard.as_markup(resize_keyboard=True)
    )

@router.message(lambda message: message.text == "📝 Оставить отзыв")
async def ask_feedback(message: Message):
    await message.answer("✍️ Напиши свой отзыв, и он будет опубликован в канале.")

@router.message()
async def handle_feedback(message: Message):
    if not message.text:
        await message.answer("⚠️ Пожалуйста, отправь только текстовый отзыв.")
        return
    username = f"@{message.from_user.username}" if message.from_user.username else "Без @"
    text = f"""📝 Новый отзыв от {username}:

{message.text}"""
    await bot.send_message(CHANNEL_ID, text)
    await message.answer("✅ Спасибо! Отзыв отправлен в канал.")

async def main():
    # Запускаем веб-приложение и бота одновременно
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()
    print("Webserver started at http://0.0.0.0:8080")

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
