import asyncio
import json
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import web
from aiogram import Router

TOKEN = "7377520849:AAE90iBIivs3iExzl1mm6QxwTt0MYDSG08I"
CHANNEL_ID = '@GarantBlox'
LOG_CHANNEL_ID = '@GarantBlox_logs'
ADMIN_ID = 1725224593

bot = Bot(token=TOKEN)
dp = Dispatcher(bot=bot)
router = Router()
dp.include_router(router)

DATA_DIR = "data"
ORDERS_FILE = os.path.join(DATA_DIR, "orders.json")
FEEDBACKS_FILE = os.path.join(DATA_DIR, "feedbacks.json")
USERS_FILE = os.path.join(DATA_DIR, "users.json")
REFERRALS_FILE = os.path.join(DATA_DIR, "referrals.json")

def load_json(filename, default):
    if not os.path.exists(filename):
        return default
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(filename, data):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

orders = load_json(ORDERS_FILE, {})
feedbacks = load_json(FEEDBACKS_FILE, [])
users = set(load_json(USERS_FILE, []))
referrals = load_json(REFERRALS_FILE, {})

feedback_waiting = set()
order_steps = {}
order_data = {}

async def handle(request):
    return web.Response(text="I'm alive!")

app = web.Application()
app.add_routes([web.get("/", handle)])

def save_all():
    save_json(ORDERS_FILE, orders)
    save_json(FEEDBACKS_FILE, feedbacks)
    save_json(USERS_FILE, list(users))
    save_json(REFERRALS_FILE, referrals)

@router.message(Command("start"))
async def start(message: Message, command: Command.Object):
    user_id = message.from_user.id
    users.add(user_id)

    if command.args and command.args.startswith("ref_"):
        try:
            inviter_id = int(command.args.split("_")[1])
            if inviter_id != user_id and str(user_id) not in referrals.get(str(inviter_id), []):
                referrals.setdefault(str(inviter_id), []).append(str(user_id))
        except Exception:
            pass

    save_all()

    keyboard = ReplyKeyboardBuilder()
    keyboard.add(types.KeyboardButton(text="📝 Оставить отзыв"))
    keyboard.add(types.KeyboardButton(text="📦 Сделать заказ гаранту"))
    keyboard.add(types.KeyboardButton(text="📖 Читать отзывы"))
    keyboard.add(types.KeyboardButton(text="📊 Мои заказы"))
    keyboard.add(types.KeyboardButton(text="🧾 Моя реферальная ссылка"))
    await message.answer(
        "Привет! 👋 Выберите действие:",
        reply_markup=keyboard.as_markup(resize_keyboard=True)
    )

@router.message(lambda m: m.text == "📝 Оставить отзыв")
async def ask_feedback(message: Message):
    feedback_waiting.add(message.chat.id)
    await message.answer("✍️ Напиши свой отзыв. После отправки он попадёт на модерацию.")

@router.message(lambda m: m.text == "📦 Сделать заказ гаранту")
async def start_order(message: Message):
    order_steps[message.chat.id] = 0
    order_data[message.chat.id] = {}
    await message.answer("📋 Шаг 1/4: Что вы хотите заказать у гаранта?")

@router.message(lambda m: m.text == "📖 Читать отзывы")
async def send_last_feedbacks(message: Message):
    approved = [f for f in feedbacks if f.get('status') == 'approved']
    if not approved:
        await message.answer("Пока нет одобренных отзывов.")
        return
    last_10 = approved[-10:]
    text = "📢 Последние отзывы:\n\n" + "\n\n".join(
        f"@{f['user']}: {f['text']}" for f in last_10
    )
    await message.answer(text)

@router.message(lambda m: m.text == "📊 Мои заказы")
async def user_orders_status(message: Message):
    user_id = message.from_user.id
    user_orders = [o for o in orders.values() if o['from_id'] == user_id]
    if not user_orders:
        await message.answer("У вас пока нет заказов.")
        return
    lines = []
    for o in user_orders:
        status = o['status']
        data = o['data']
        desc = data.get('description', 'Нет описания')
        lines.append(f"Заказ: {desc}\nСтатус: {status}")
    await message.answer("\n\n".join(lines))

@router.message(lambda m: m.text == "🧾 Моя реферальная ссылка")
async def send_ref_link(message: Message):
    user_id = message.from_user.id
    ref_link = f"https://t.me/YourBotUsername?start=ref_{user_id}"  # Заменить YourBotUsername на имя бота
    count_invited = len(referrals.get(str(user_id), []))
    await message.answer(
        f"Ваша реферальная ссылка:\n{ref_link}\n\n"
        f"Приглашено пользователей: {count_invited}"
    )

@router.message(Command("cancel"))
async def cmd_cancel(message: Message):
    chat_id = message.chat.id
    if chat_id in feedback_waiting:
        feedback_waiting.remove(chat_id)
        await message.answer("Отзыв отменён.")
    elif chat_id in order_steps:
        order_steps.pop(chat_id)
        order_data.pop(chat_id, None)
        await message.answer("Заказ отменён.")
    else:
        await message.answer("Нет активных действий для отмены.")

@router.message(F.text)
async def handle_text(message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    text = message.text.strip()

    if chat_id in feedback_waiting:
        feedback_waiting.remove(chat_id)
        feedbacks.append({
            "user": message.from_user.username or "Без_ника",
            "text": text,
            "status": "pending"
        })
        save_all()
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Одобрить", callback_data=f"approve_feedback:{len(feedbacks)-1}"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_feedback:{len(feedbacks)-1}")
            ]
        ])
        await bot.send_message(ADMIN_ID, f"📝 Новый отзыв на модерацию от @{message.from_user.username or 'Без_ника'}:\n\n{text}", reply_markup=keyboard)
        await message.answer("Спасибо! Ваш отзыв отправлен на модерацию.")
        return

    if chat_id in order_steps:
        step = order_steps[chat_id]

        if step == 0:
            order_data[chat_id]['description'] = text
            order_steps[chat_id] = 1
            await message.answer("📋 Шаг 2/4: Укажи сумму (числом)")
            return

        elif step == 1:
            if not text.isdigit():
                await message.answer("Пожалуйста, введи сумму числом.")
                return
            order_data[chat_id]['amount'] = int(text)
            order_steps[chat_id] = 2
            await message.answer("📋 Шаг 3/4: От кого заказ?")
            return

        elif step == 2:
            order_data[chat_id]['from_whom'] = text
            order_steps[chat_id] = 3
            await message.answer("📋 Шаг 4/4: Ссылка на профиль (если есть, иначе напиши '-' )")
            return

        elif step == 3:
            order_data[chat_id]['profile_link'] = text
            order_id = f"{user_id}_{message.message_id}"
            orders[order_id] = {
                'from_id': user_id,
                'data': order_data[chat_id],
                'status': 'Ожидает рассмотрения'
            }
            save_all()

            order_text = (
                f"📦 Новый заказ от @{message.from_user.username or 'Без_ника'}:\n"
                f"Описание: {order_data[chat_id]['description']}\n"
                f"Сумма: {order_data[chat_id]['amount']}\n"
                f"От кого: {order_data[chat_id]['from_whom']}\n"
                f"Профиль: {order_data[chat_id]['profile_link']}"
            )

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Принять", callback_data=f"accept:{order_id}"),
                    InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject:{order_id}")
                ]
            ])

            await bot.send_message(ADMIN_ID, order_text, reply_markup=keyboard)
            await bot.send_message(LOG_CHANNEL_ID, f"🆕 Новый заказ:\n{order_text}")
            await message.answer("📨 Ваш заказ отправлен гаранту. Ожидайте ответа.")
            order_steps.pop(chat_id)
            order_data.pop(chat_id, None)
            return

@router.callback_query(F.data.startswith("accept:"))
async def handle_accept(callback: CallbackQuery):
    order_id = callback.data.split(":")[1]
    order = orders.get(order_id)
    if not order:
        await callback.answer("⛔ Заказ не найден.", show_alert=True)
        return

    order['status'] = 'Принят'
    save_all()

    await bot.send_message(order['from_id'], "✅ Ваш заказ принят! Свяжитесь с гарантом: @Dio_Brando_Za_Warudo")
    await callback.message.edit_text(callback.message.text + "\n\n✅ Заказ принят.")
    await bot.send_message(LOG_CHANNEL_ID, f"✅ Заказ {order_id} принят.")
    await callback.answer("Вы приняли заказ.")

@router.callback_query(F.data.startswith("reject:"))
async def handle_reject(callback: CallbackQuery):
    order_id = callback.data.split(":")[1]
    order = orders.get(order_id)
    if not order:
        await callback
