import os
import json
import asyncio
import logging
import urllib.parse
from datetime import date
from google import genai
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, CommandObject, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

logging.basicConfig(level=logging.INFO)

# 🔑 Танзимоти асосӣ
TELEGRAM_TOKEN = "8949334224:AAEip9Lbdxd2YFwS_rNNNls2vxaN6qkvfDc"
ADMIN_ID = "8419536226"  # ID-и шумо (Муҳаммадҷон)
BOT_USERNAME = "Filmyob_bot"
CHANNEL_USERNAME = "@filmyob_channel"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

TEMP_DIR = "temp_videos"
DATA_FILE = "users_data.json"
os.makedirs(TEMP_DIR, exist_ok=True)

# Луғати матнҳо барои 3 забон
TEXTS = {
    "tg": {
        "welcome": "Салом! 🎬 Бот омодаи кор аст. Видеоро фиристед!",
        "menu_profile": "📊 Ҳисоби ман",
        "menu_lang": "🌐 Забон / Язык / Language",
        "select_lang": "Лутфан забонро интихоб кунед:",
        "lang_set": "✅ Забон ба Тоҷикӣ иваз карда шуд!",
        "limit_end": "🛑 Лимити имрӯза тамом шуд!",
    },
    "ru": {
        "welcome": "Привет! 🎬 Бот готов к работе. Отправьте видео!",
        "menu_profile": "📊 Мой профиль",
        "menu_lang": "🌐 Забон / Язык / Language",
        "select_lang": "Пожалуйста, выберите язык:",
        "lang_set": "✅ Язык изменен на Русский!",
        "limit_end": "🛑 Дневной лимит исчерпан!",
    },
    "en": {
        "welcome": "Hello! 🎬 Bot is ready. Send a video!",
        "menu_profile": "📊 My Profile",
        "menu_lang": "🌐 Забон / Язык / Language",
        "select_lang": "Please select a language:",
        "lang_set": "✅ Language changed to English!",
        "limit_end": "🛑 Daily limit reached!",
    }
}

# ─── ТУГМАҲОИ МЕНЮ ───
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📊 Ҳисоби ман (Профиль)")],
        [KeyboardButton(text="📜 Қоидаҳо ва Линки рефералӣ")]
    ],
    resize_keyboard=True
)

# ─── БАЗАИ МАЪЛУМОТ ───
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def get_user_data(user_id: str):
    data = load_data()
    today = str(date.today())
    if user_id not in data:
        data[user_id] = {"referrals": [], "bonus_videos": 0, "daily_date": today, "daily_count": 0}
    elif data[user_id].get("daily_date") != today:
        data[user_id]["daily_date"] = today
        data[user_id]["daily_count"] = 0
    save_data(data)
    return data

async def check_sub(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in ["creator", "administrator", "member"]
    except:
        return True

# ─── ХАБАРДОР КАРДАНИ КОРБАРОН ВАҚТИ РӮШАН ШУДАНИ БОТ ───
async def notify_users_on_restart():
    data = load_data()
    start_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Оғоз кардан (Start)", url=f"https://t.me/{BOT_USERNAME}?start=restart")]
    ])
    
    restart_text = (
        "🔄 **Бот навсозӣ шуд!**\n\n"
        "Лутфан барои идомаи кор ва навсозии меню тугмаи зерро пахш кунед ё бугузоред: /start"
    )
    
    for user_id in data.keys():
        try:
            await bot.send_message(chat_id=int(user_id), text=restart_text, reply_markup=start_kb, parse_mode="Markdown")
            await asyncio.sleep(0.05)  # Барои он ки Бот аз тарафи Телеграм блок нашавад
        except Exception:
            pass  # Агар корбар ботро блок карда бошад, хатогиро сарфи назар мекунад

# ─── 1. COMMAND /START ───
@dp.message(CommandStart())
async def start_cmd(message: types.Message, command: CommandObject):
    user_id = str(message.from_user.id)
    get_user_data(user_id)
    
    referrer_id = command.args
    if referrer_id and referrer_id != user_id and referrer_id != "restart":
        all_data = load_data()
        if referrer_id in all_data and user_id not in all_data[referrer_id]["referrals"]:
            all_data[referrer_id]["referrals"].append(user_id)
            if len(all_data[referrer_id]["referrals"]) % 2 == 0:
                all_data[referrer_id]["bonus_videos"] += 1
                try: 
                    await bot.send_message(int(referrer_id), "🎉 **Табрик!** Шумо 2 дӯстатонро даъват кардед ва +1 видеои бонусӣ гирифтед!")
                except: 
                    pass
            save_data(all_data)

    if not await check_sub(message.from_user.id):
        sub_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Аъзо шудан ба канал", url=f"https://t.me/filmyob_channel")],
            [InlineKeyboardButton(text="✅ Аъзо шудам", callback_data="check_subscription")]
        ])
        await message.answer("⚠️ Барои истифодаи бот, аввал ба канали мо аъзо шавед!", reply_markup=sub_kb)
        return

    rules_text = (
        f"Салом {message.from_user.first_name}! 🎬\n\n"
        f"📜 **ҚОИДАҲОИ БОТ:**\n"
        f"1️⃣ Ҳаҷми видео: то **19 МБ** (калонтар бошад, автоматӣ пок мешавад).\n"
        f"2️⃣ Лимити рӯзона: **3 видео**.\n"
        f"3️⃣ **Бонус:** Барои 2 дӯсти даъваткарда, **+1 видео** мегиред!\n\n"
        f"👇 Менюи зерро истифода баред ва видеоро фиристед!"
    )
    await message.answer(rules_text, reply_markup=main_keyboard, parse_mode="Markdown")

# ─── 2. CALLBACK ДАЪВАТИ КАНАЛ ───
@dp.callback_query(F.data == "check_subscription")
async def check_sub_callback(call: types.CallbackQuery):
    if await check_sub(call.from_user.id):
        await call.message.delete()
        await call.message.answer("✅ Тасдиқ шуд! Боз як бор /start-ро пахш кунед.")
    else:
        await call.answer("❌ Шумо ҳанӯз аъзо нашудаед!", show_alert=True)

# ─── 3. COMMAND /ADMIN ───
@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if str(message.from_user.id) != ADMIN_ID:
        return
    data = load_data()
    user_count = len(data)
    await message.answer(f"👑 **ПАНЕЛИ АДМИН**\n\n👥 Шумораи умумии корбарон: {user_count}")

# ─── 4. ТУГМАИ ПРОФИЛЬ ───
@dp.message(F.text == "📊 Ҳисоби ман (Профиль)")
async def profile_cmd(message: types.Message):
    user_id = str(message.from_user.id)
    all_data = get_user_data(user_id)
    u_data = all_data[user_id]
    
    daily_left = max(0, 3 - u_data["daily_count"])
    bonus_left = u_data["bonus_videos"]
    ref_count = len(u_data["referrals"])
    
    admin_note = " (👑 Админ - беохир)" if user_id == ADMIN_ID else ""
    
    profile_text = (
        f"👤 **Профили шумо:** {message.from_user.first_name}{admin_note}\n"
        f"🆔 **ID:** `{user_id}`\n\n"
        f"📅 **Лимити имрӯза:** {daily_left} аз 3 видео\n"
        f"🎁 **Видеоҳои бонусӣ:** {bonus_left} адад\n"
        f"👥 **Дӯстони даъватшуда:** {ref_count} нафар"
    )
    await message.answer(profile_text, parse_mode="Markdown")

# ─── 5. ТУГМАИ ҚОИДАҲО ВА РЕФЕРАЛ ───
@dp.message(F.text == "📜 Қоидаҳо ва Линки рефералӣ")
async def info_cmd(message: types.Message):
    user_id = str(message.from_user.id)
    ref_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
    rules_text = (
        f"📜 **ҚОИДАҲОИ БОТ:**\n"
        f"1️⃣ Ҳаҷми видео: то **19 МБ**.\n"
        f"2️⃣ Лимити рӯзона: **3 видео**.\n"
        f"3️⃣ Барои 2 дӯст = **+1 видеои бонусӣ**.\n\n"
        f"🔗 **Линки рефералии шумо:**\n`{ref_link}`"
    )
    await message.answer(rules_text, parse_mode="Markdown")

# ─── 6. КОРКАРДИ ВИДЕОҲО ───
@dp.message(F.video | F.video_note)
async def handle_video(message: types.Message):
    user_id = str(message.from_user.id)
    
    if not await check_sub(message.from_user.id):
        await start_cmd(message, CommandObject(command="start"))
        return

    video_obj = message.video or message.video_note
    if video_obj.file_size > 19 * 1024 * 1024:
        try: await message.delete()
        except: pass
        await message.answer("⚠️ **Видео пок шуд!** Ҳаҷм аз 19 МБ зиёд аст.")
        return

    # Тафтиши лимит танҳо барои корбарони оддӣ (Админ лимит надорад)
    if user_id != ADMIN_ID:
        all_data = get_user_data(user_id)
        u_data = all_data[user_id]
        
        daily_left = 3 - u_data["daily_count"]
        bonus_left = u_data["bonus_videos"]

        if daily_left <= 0 and bonus_left <= 0:
            ref_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
            await message.answer(
                f"🛑 **Лимити имрӯза тамом шуд!**\n\n"
                f"🎁 Барои +1 видео, дӯстонро даъват кунед:\n`{ref_link}`",
                parse_mode="Markdown"
            )
            return

        if daily_left > 0:
            u_data["daily_count"] += 1
        else:
            u_data["bonus_videos"] -= 1
        save_data(all_data)

    status_msg = await message.answer("📥 Видео қабул шуд. Таҳлил рафта истодааст...")
    file_info = await bot.get_file(video_obj.file_id)
    video_path = os.path.join(TEMP_DIR, f"{user_id}.mp4")
    await bot.download_file(file_info.file_path, destination=video_path)
    
    try:
        uploaded_file = client.files.upload(file=video_path)
        while uploaded_file.state.name == "PROCESSING":
            await asyncio.sleep(2)
            uploaded_file = client.files.get(name=uploaded_file.name)

        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=[uploaded_file, "Determine the full feature length movie title (not TV series or short clip). Write ONLY the official movie title in Russian."]
        )
        movie_name = response.text.strip()
        client.files.delete(name=uploaded_file.name)
        
        enc = urllib.parse.quote(movie_name)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="▶️ YouTube", url=f"https://www.youtube.com/results?search_query=фильм+{enc}+смотреть+полностью")],
            [InlineKeyboardButton(text="🌐 Google", url=f"https://www.google.com/search?q=смотреть+фильм+{enc}+в+хорошем+качестве")]
        ])
        await status_msg.edit_text(f"🎬 Номи филм:\n\n{movie_name}", reply_markup=keyboard)
    except Exception as e:
        await status_msg.edit_text(f"❌ Хатогӣ: {e}")
    finally:
        if os.path.exists(video_path): os.remove(video_path)

# ─── 7. CATCH-ALL ХЕНДЛЕР БАРОИ ПАЁМҲОИ ДИГАР ───
@dp.message()
async def unhandled_messages(message: types.Message):
    await message.answer("ℹ️ Лутфан танҳо **пачаи видео** (кино)-ро фиристед ё тугмаҳои менюро истифода баред.")

# ─── ИҶРОҲОИ АВВАЛИН ВА СТАРТ ───
async def main():
    dp.startup.register(notify_users_on_restart)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
