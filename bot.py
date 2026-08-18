import os
import json
import asyncio
import logging
import urllib.parse
from datetime import date
from google import genai
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

logging.basicConfig(level=logging.INFO)

# 🔑 Танзимоти асосӣ
TELEGRAM_TOKEN = "8949334224:AAEip9Lbdxd2YFwS_rNNNls2vxaN6qkvfDc"
BOT_USERNAME = "Filmyob_bot"
CHANNEL_USERNAME = "@filmyob_channel"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

TEMP_DIR = "temp_videos"
DATA_FILE = "users_data.json"
os.makedirs(TEMP_DIR, exist_ok=True)

# ─── ТУГМАҲОИ МЕНЮ (REPLY KEYBOARD) ───
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

# ─── /START ───
@dp.message(CommandStart())
async def start_cmd(message: types.Message, command: CommandObject):
    user_id = str(message.from_user.id)
    get_user_data(user_id)
    
    referrer_id = command.args
    if referrer_id and referrer_id != user_id:
        all_data = load_data()
        if referrer_id in all_data and user_id not in all_data[referrer_id]["referrals"]:
            all_data[referrer_id]["referrals"].append(user_id)
            if len(all_data[referrer_id]["referrals"]) % 2 == 0:
                all_data[referrer_id]["bonus_videos"] += 1
                try: await bot.send_message(int(referrer_id), "🎉 **Табрик!** Шумо 2 дӯстатонро даъват кардед ва +1 видеои бонусӣ гирифтед!")
                except: pass
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
        f"👇 Менюи зерро истифода баред ва парчаи видеоро фиристед!"
    )
    await message.answer(rules_text, reply_markup=main_keyboard, parse_mode="Markdown")

@dp.callback_query(F.data == "check_subscription")
async def check_sub_callback(call: types.CallbackQuery):
    if await check_sub(call.from_user.id):
        await call.message.delete()
        await call.message.answer("✅ Тасдиқ шуд! Боз як бор /start-ро пахш кунед.")
    else:
        await call.answer("❌ Шумо ҳанӯз аъзо нашудаед!", show_alert=True)

# ─── ТУГМАИ ТАФТИШИ ЧАНД ВИДЕО ДОРАД (ПРОФИЛЬ) ───
@dp.message(F.text == "📊 Ҳисоби ман (Профиль)")
async def profile_cmd(message: types.Message):
    user_id = str(message.from_user.id)
    all_data = get_user_data(user_id)
    u_data = all_data[user_id]
    
    daily_left = 3 - u_data["daily_count"]
    if daily_left < 0:
        daily_left = 0
    bonus_left = u_data["bonus_videos"]
    ref_count = len(u_data["referrals"])
    
    profile_text = (
        f"👤 **Профили шумо:** {message.from_user.first_name}\n"
        f"🆔 **ID:** `{user_id}`\n\n"
        f"📅 **Лимити имрӯза:** {daily_left} аз 3 видео\n"
        f"🎁 **Видеоҳои бонусӣ:** {bonus_left} адад\n"
        f"👥 **Дӯстони даъватшуда:** {ref_count} нафар\n\n"
        f"💡 *Рӯзи нав лимити 3-видеоии шумо худаш барқарор мешавад!*"
    )
    await message.answer(profile_text, parse_mode="Markdown")

# ─── ТУГМАИ ҚОИДАҲО ВА РЕФЕРАЛ ───
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

# ─── КОРКАРДИ ВИДЕО ───
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

    all_data = get_user_data(user_id)
    u_data = all_data[user_id]
    
    daily_left = 3 - u_data["daily_count"]
    bonus_left = u_data["bonus_videos"]

    if daily_left <= 0 and bonus_left <= 0:
        ref_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
        await message.answer(
            f"🛑 **Лимити имрӯзаи шумо тамом шуд! (0 аз 3 боқӣ монд)**\n\n"
            f"🎁 Барои гирифтани **+1 видеои иловагӣ**, 2 дӯстатонро даъват кунед:\n`{ref_link}`",
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

if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))
