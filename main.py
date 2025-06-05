
import asyncio
from aiogram import Bot, Dispatcher, types
from aiohttp import web

TOKEN = "7377520849:AAFKMxzbjJfQfSc-SWI0QAFG7JzYWcax8bQ"
CHANNEL_ID = '@GarantBlox'

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Веб-хендлер для проверки, что сервер живой
async def handle(request):
    return web.Response(text="I'm alive!")

app = web.Application()
app.add_routes([web.get("/", handle)])

@dp.message(commands=["start"])
async def start(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton("📝 Оставить отзыв"))
    await message.answer(
        "Привет! 👋 Здесь ты можешь оставить отзыв о работе гаранта GarantBlox.",
        reply_markup=keyboard
    )

@dp.message(lambda message: message.text == "📝 Оставить отзыв")
async def ask_feedback(message: types.Message):
    await message.answer("✍️ Напиши свой отзыв, и он будет опубликован в канале.")

@dp.message()
async def handle_feedback(message: types.Message):
    if not message.text:
        await message.answer("⚠️ Пожалуйста, отправь только текстовый отзыв.")
        return
    username = f"@{message.from_user.username}" if message.from_user.username else "Без @"
    text = f"""📝 Новый отзыв от {username}:

{message.text}"""
    await bot.send_message(CHANNEL_ID, text)
    await message.answer("✅ Спасибо! Отзыв отправлен в канал.")

async def main():
    # Зарегистрируем бота в диспетчере
    await dp.start_polling(bot)

async def start_web_app():
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()
    print("Webserver started at http://0.0.0.0:8080")

async def main_runner():
    await asyncio.gather(start_web_app(), main())

if __name__ == "__main__":
    asyncio.run(main_runner())
