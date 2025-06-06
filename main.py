import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import web
from aiogram import Router

TOKEN = "ТВОЙ_ТОКЕН_ЗДЕСЬ"
CHANNEL_ID = '@GarantBlox'  # убедись, что бот админ в этом канале
ADMIN_ID = 1725224593  # Telegram user_id гаранта

bot = Bot(token=TOKEN)
dp = Dispatcher(bot=bot)
router = Router()
dp.include_router(router)

orders = {}
feedback_waiting = set()  # для отслеживания, кто пишет отзыв

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
        "Привет! 👋 Здесь ты можешь оставить отзыв или сделать заказ гаранту.",
        reply_markup=keyboard.as_markup(resize_keyboard=True)
    )

@router.message(lambda message: message.text == "📝 Оставить отзыв")
async def ask_feedback(message: Message):
    feedback_waiting.add(message.chat.id)
    await message.answer("✍️ Напиши свой отзыв, и он будет опубликован в канале.")

@router.message(lambda message: message.text == "📦 Сделать заказ гаранту")
async def ask_order(message: Message):
    await message.answer("📋 Напиши, что ты хочешь заказать у гаранта.")

@router.message(Command("command2"))
async def send_channel(message: Message):
    await message.answer(f"📢 Наш канал: {CHANNEL_ID}")

@router.message(F.text)
async def handle_text(message: Message):
    # Если пользователь в режиме написания отзыва
    if message.chat.id in feedback_waiting:
        await bot.send_message(
            CHANNEL_ID,
            f"📝 Новый отзыв от @{message.from_user.username or 'Без_ника'}:\n\n{message.text}"
        )
        await message.answer("Спасибо за отзыв! Он опубликован в канале.")
        feedback_waiting.remove(message.chat.id)
        return

    if message.reply_to_message:
        return

    if message.text.startswith("📋") or message.text.startswith("✍️"):
        return

    # Обрабатываем заказ
    order_id = f"{message.chat.id}_{message.message_id}"
    orders[order_id] = {
        'from_id': message.from_user.id,
        'text': message.text
    }

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Принять", callback_data=f"accept:{order_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject:{order_id}")
        ]
    ])

    await bot.send_message(
        ADMIN_ID,
        f"🆕 Новый заказ от @{message.from_user.username or 'Без_ника'}:\n\n{message.text}",
        reply_markup=keyboard
    )
    await message.answer("📨 Ваш заказ отправлен гаранту. Ожидайте ответа.")

@router.callback_query(F.data.startswith("accept:"))
async def handle_accept(callback: CallbackQuery):
    order_id = callback.data.split(":")[1]
    order = orders.get(order_id)
    if not order:
        await callback.answer("⛔ Заказ не найден.", show_alert=True)
        return

    await bot.send_message(order['from_id'], "✅ Ваш заказ принят! Свяжитесь с гарантом: @Dio_Brando_Za_Warudo")
    await callback.message.edit_text(callback.message.text + "\n\n✅ Заказ принят.")
    await callback.answer("Вы приняли заказ.")

@router.callback_query(F.data.startswith("reject:"))
async def handle_reject(callback: CallbackQuery):
    order_id = callback.data.split(":")[1]
    order = orders.get(order_id)
    if not order:
        await callback.answer("⛔ Заказ не найден.", show_alert=True)
        return

    await bot.send_message(order['from_id'], "❌ Ваш заказ отклонён. Вы можете попробовать позже.")
    await callback.message.edit_text(callback.message.text + "\n\n❌ Заказ отклонён.")
    await callback.answer("Вы отклонили заказ.")

async def main():
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()
    print("Webserver started at http://0.0.0.0:8080")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
