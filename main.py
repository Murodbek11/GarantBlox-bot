import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import web
from aiogram import Router

TOKEN = "7377520849:AAEz3J_WmHV6kDOdpDaryoWVoVbdlSKKmLw"

CHANNEL_ID = -1002567963097       # Основной канал @GarantBlox
LOG_CHANNEL_ID = -1002664591140   # Лог-канал @GarantBlox_logs
ADMIN_ID = 1725224593             # Telegram user_id гаранта

bot = Bot(token=TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

orders = {}
feedbacks = {}
user_states = {}       # Хранит состояния пользователей: awaiting_feedback, awaiting_order и т.п.
order_categories = {}  # Хранит выбранные категории заказов по user_id

# Веб-хендлер для проверки, что сервер живой
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

@router.message(F.text == "📝 Оставить отзыв")
async def ask_feedback(message: Message):
    user_states[message.from_user.id] = "awaiting_feedback"
    await message.answer("✍️ Напиши свой отзыв, и он будет отправлен на модерацию.")

@router.message(F.text == "📦 Сделать заказ гаранту")
async def ask_order_category(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Трейд редких предметов", callback_data="category:1"),
            InlineKeyboardButton(text="Трейд аккаунтов", callback_data="category:2"),
        ],
    ])
    await message.answer("📂 Выбери категорию заказа:", reply_markup=keyboard)

@router.callback_query(F.data.startswith("category:"))
async def category_chosen(callback: CallbackQuery):
    category = callback.data.split(":")[1]
    user_id = callback.from_user.id
    order_categories[user_id] = category
    user_states[user_id] = "awaiting_order"

    category_names = {
        "1": "Трейд редких предметов",
        "2": "Трейд аккаунтов"
    }

    await callback.message.edit_text(f"Вы выбрали категорию: {category_names.get(category, 'Неизвестная')}. Теперь опиши, что хочешь заказать у гаранта.")
    await callback.answer()

@router.message(F.text)
async def handle_text(message: Message):
    if message.reply_to_message:
        return

    state = user_states.get(message.from_user.id)

    if state == "awaiting_feedback":
        feedback_id = f"{message.chat.id}_{message.message_id}"
        feedbacks[feedback_id] = {
            'from_id': message.from_user.id,
            'text': message.text,
            'username': message.from_user.username or "Без ника"
        }

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Одобрить", callback_data=f"approve_feedback:{feedback_id}"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_feedback:{feedback_id}")
            ]
        ])

        await bot.send_message(
            LOG_CHANNEL_ID,
            f"📝 Новый отзыв от @{feedbacks[feedback_id]['username']}:\n\n{message.text}",
            reply_markup=keyboard
        )
        await message.answer("📨 Спасибо! Твой отзыв отправлен на модерацию.")
        user_states.pop(message.from_user.id, None)
        return

    elif state == "awaiting_order":
        user_id = message.from_user.id
        category = order_categories.get(user_id, "Не указана")
        category_names = {
            "1": "Трейд редких предметов",
            "2": "Трейд аккаунтов"
        }
        order_id = f"{message.chat.id}_{message.message_id}"
        orders[order_id] = {
            'from_id': user_id,
            'text': message.text,
            'username': message.from_user.username or "Без ника",
            'category': category_names.get(category, "Не указана")
        }

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Принять", callback_data=f"accept_order:{order_id}"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_order:{order_id}")
            ]
        ])

        await bot.send_message(
            ADMIN_ID,
            f"📦 Новый заказ (Категория: {orders[order_id]['category']}) от @{orders[order_id]['username']}:\n\n{message.text}",
            reply_markup=keyboard
        )
        await message.answer("📨 Ваш заказ отправлен гаранту. Ожидайте ответа.")
        user_states.pop(user_id, None)
        order_categories.pop(user_id, None)
        return

    await message.answer("❗ Пожалуйста, выберите действие на клавиатуре перед отправкой сообщения.")

@router.callback_query(F.data.startswith("accept_order:"))
async def handle_accept_order(callback: CallbackQuery):
    order_id = callback.data.split(":")[1]
    order = orders.get(order_id)
    if not order:
        await callback.answer("⛔ Заказ не найден.", show_alert=True)
        return

    await bot.send_message(order['from_id'], "✅ Ваш заказ принят! Свяжитесь с гарантом: @Dio_Brando_Za_Warudo")
    await callback.message.edit_text(callback.message.text + "\n\n✅ Заказ принят.")
    await callback.answer("Вы приняли заказ.")

@router.callback_query(F.data.startswith("reject_order:"))
async def handle_reject_order(callback: CallbackQuery):
    order_id = callback.data.split(":")[1]
    order = orders.get(order_id)
    if not order:
        await callback.answer("⛔ Заказ не найден.", show_alert=True)
        return

    await bot.send_message(order['from_id'], "❌ Ваш заказ отклонён. Вы можете попробовать позже.")
    await callback.message.edit_text(callback.message.text + "\n\n❌ Заказ отклонён.")
    await callback.answer("Вы отклонили заказ.")

@router.callback_query(F.data.startswith("approve_feedback:"))
async def handle_approve_feedback(callback: CallbackQuery):
    feedback_id = callback.data.split(":")[1]
    feedback = feedbacks.get(feedback_id)
    if not feedback:
        await callback.answer("⛔ Отзыв не найден.", show_alert=True)
        return

    text = feedback.get('text', '')
    username = feedback.get('username', 'Без ника')

    await bot.send_message(CHANNEL_ID, f"📝 Отзыв от @{username}:\n\n{text}")
    await callback.message.edit_text(f"✅ Отзыв от @{username} одобрен.")
    await callback.answer("Отзыв одобрен.")

@router.callback_query(F.data.startswith("reject_feedback:"))
async def handle_reject_feedback(callback: CallbackQuery):
    feedback_id = callback.data.split(":")[1]
    feedback = feedbacks.get(feedback_id)
    if not feedback:
        await callback.answer("⛔ Отзыв не найден.", show_alert=True)
        return

    username = feedback.get('username', 'Без ника')

    await bot.send_message(feedback['from_id'], "❌ Ваш отзыв отклонён. Спасибо за понимание.")
    await callback.message.edit_text(f"❌ Отзыв от @{username} отклонён.")
    await callback.answer("Отзыв отклонён.")

async def main():
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()
    print("Webserver started at http://0.0.0.0:8080")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
