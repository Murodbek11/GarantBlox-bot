import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiohttp import web

TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = '@GarantBlox'

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

async def handle(request):
    return web.Response(text="I'm alive!")

app = web.Application()
app.add_routes([web.get('/', handle)])

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton("📝 Оставить отзыв"))
    await message.answer(
        "Привет! 👋
Здесь ты можешь оставить отзыв о работе гаранта GarantBlox.",
        reply_markup=keyboard
    )
    @dp.message_handler(lambda message: message.text == "📝 Оставить отзыв")
async def ask_feedback(message: types.Message):
    await message.answer("✍️ Напиши свой отзыв, и он будет опубликован в канале.")

@dp.message_handler()
async def handle_feedback(message: types.Message):
    username = f"@{message.from_user.username}" if message.from_user.username else "Без @"
    text = f"📝 Новый отзыв от {username}:

{message.text}"
    await bot.send_message(CHANNEL_ID, text)
    await message.answer("✅ Спасибо! Отзыв отправлен в канал.")

async def main():
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    await dp.start_polling()

if __name__ == '__main__':
    asyncio.run(main())
