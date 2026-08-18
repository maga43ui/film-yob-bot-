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
ADMIN_ID = "123456789" # <--- ИНҶО ID-И ХУДРО ГУЗОР (МАСАЛАН: "987654321")
BOT_USERNAME = "Filmyob_bot"
CHANNEL_USERNAME = "@filmyob_channel"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

TEMP_DIR = "temp_videos"
DATA_FILE = "users_data.json"
os.makedirs(TEMP_DIR, exist_ok=True)

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

# ─── ПАНЕЛИ АДМИН (/admin) ───
@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if str(message.from_user.id) != ADMIN_ID:
        return
    data = load_data()
    user_count = len(data)
    await message.answer(f"👑 **ПАНЕЛИ АДМИН**\n\n👥 Шумораи умумии корбарон: {user_count}")

# ─── КОРКАРДИ ВИДЕО (БО ЛИМИТИ БЕОХИР БАРОИ АДМИН) ───
@dp.message(F.video | F.video_note)
async def handle_video(message: types.Message):
    user_id = str(message.from_user.id)
    
    # Агар админ набошад, лимитро тафтиш мекунем
    if user_id != 8419536226:
        # Лимит барои корбарони оддӣ (3 видео)
        all_data = get_user_data(user_id)
        u_data = all_data[user_id]
        
        daily_left = 3 - u_data["daily_count"]
        bonus_left = u_data["bonus_videos"]

        if daily_left <= 0 and bonus_left <= 0:
            ref_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
            await message.answer("🛑 **Лимити имрӯза тамом шуд!** Барои +1 видео, дӯстонро даъват кунед.")
            return

        if daily_left > 0: u_data["daily_count"] += 1
        else: u_data["bonus_videos"] -= 1
        save_data(all_data)

    # Иҷрои таҳлил (барои ҳама, админ ё корбар)
    status_msg = await message.answer("📥 Таҳлил рафта истодааст...")
    video_obj = message.video or message.video_note
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
            contents=[uploaded_file, "Determine the movie title. Write ONLY the movie title."]
        )
        movie_name = response.text.strip()
        client.files.delete(name=uploaded_file.name)
        
        await status_msg.edit_text(f"🎬 Номи филм: {movie_name}")
    except Exception as e:
        await status_msg.edit_text(f"❌ Хатогӣ: {e}")
    finally:
        if os.path.exists(video_path): os.remove(video_path)

if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))
