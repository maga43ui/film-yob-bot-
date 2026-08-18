import os
import json
import asyncio
import logging
import urllib.parse
from datetime import date
from google import genai
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

logging.basicConfig(level=logging.INFO)

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

# ─── БАЗАИ МАЪЛУМОТ (JSON) ───
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
        data[user_id] = {
            "referrals": [],
            "bonus_videos": 0,
            "daily_date": today,
            "daily_count": 0
        }
    else:
        if data[user_id].get("daily_date") != today:
            data[user_id]["daily_date"] = today
            data[user_id]["daily_count"] = 0
    save_data(data)
    return data

async def check_sub(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in ["creator", "administrator", "member"]
    except Exception as e:
        logging.error(f"Хатогии тафтиши аъзошавӣ: {e}")
        return True

# ─── ИШКОРКАРДИ /START ───
@dp.message(CommandStart())
async def start_cmd(message: types.Message, command: CommandObject):
    user_id = str(message.from_user.id)
    data = get_user_data(user_id)
    
    referrer_id = command.args
    if referrer_id and referrer_id != user_id:
        all_data = load_data()
        if referrer_id in all_data and user_id not in all_data[referrer_id]["referrals"]:
            all_data[referrer_id]["referrals"].append(user_id)
            
            # Агар 2 дӯстро даъват карда бошад = +1 видеои бонус
            if len(all_data[referrer_id]["referrals"]) % 2 == 0:
                all_data[referrer_id]["bonus_videos"] += 1
                try:
                    await bot.send_message(
                        chat_id=int(referrer_id),
                        text="🎉 **Табрик!** Шумо 2 дӯстатонро даъват кардед ва **+1 видеои мукофотӣ** гирифтед!"
                    )
                except Exception:
                    pass
            save_data(all_data)

    is_subbed = await check_sub(message.from_user.id)
    if not is_subbed:
        sub_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Аъзо шудан ба канал", url=f"https://t.me/filmyob_channel")],
            [InlineKeyboardButton(text="✅ Аъзо шудам", callback_data="check_subscription")]
        ])
        await message.answer(
            f"Салом {message.from_user.first_name}! 🎬\n\n"
            f"⚠️ Барои истифодабарии бот, аввал ба канали мо аъзо шавед!",
            reply_markup=sub_kb
        )
        return

    ref_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
    rules_text = (
        f"Салом {message.from_user.first_name}! 🎬\n\n"
        f"📜 **ҚОИДАҲОИ БОТ:**\n"
        f"1️⃣ Ҳаҷми видео набояд аз **19 МБ** зиёд бошад (видеоҳои калон автоматӣ пок мешаванд).\n"
        f"2️⃣ Лимити рӯзона: **5 видео дар 1 рӯз**.\n"
        f"3️⃣ **Бонус:** Линки худро ба дӯстон фиристед. Агар 2 дӯст даъват кунед, **+1 видеои иловагӣ** мегиред!\n\n"
        f"🔗 **Линки рефералии шумо:**\n`{ref_link}`\n\n"
        f"📥 Парчаи видеоро (2-20 сония) фиристед!"
    )
    await message.answer(rules_text, parse_mode="Markdown")

@dp.callback_query(F.data == "check_subscription")
async def check_sub_callback(call: types.CallbackQuery):
    if await check_sub(call.from_user.id):
        await call.message.delete()
        await call.message.answer("✅ **Аъзошавӣ тасдиқ шуд!** Боз як бор /start-ро пахш кунед.")
    else:
        await call.answer("❌ Шумо ҳанӯз ба канал аъзо нашудаед!", show_alert=True)

# ─── КОРКАРДИ ВИДЕО ───
@dp.message(F.video | F.video_note)
async def handle_video(message: types.Message):
    user_id = str(message.from_user.id)
    is_subbed = await check_sub(message.from_user.id)
    if not is_subbed:
        await start_cmd(message, CommandObject(command="start"))
        return

    video_obj = message.video or message.video_note

    # 1. Тафтиши ҳаҷм (>19MB -> Авто-удалить)
    MAX_SIZE = 19 * 1024 * 1024 
    if video_obj.file_size and video_obj.file_size > MAX_SIZE:
        try:
            await message.delete()
        except Exception:
            pass
        await message.answer("⚠️ **Видео пок карда шуд!** Ҳаҷми видео аз 19 МБ калон аст.")
        return

    # 2. Тафтиши лимит
    all_data = get_user_data(user_id)
    u_data = all_data[user_id]
    
    daily_left = 5 - u_data["daily_count"]
    bonus_left = u_data["bonus_videos"]

    if daily_left <= 0 and bonus_left <= 0:
        ref_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
        await message.answer(
            "🛑 **Лимити имрӯзаи шумо тамом шуд! (5/5)**\n\n"
            "🎁 Барои гирифтани **+1 видеои иловагӣ**, 2 дӯстатонро даъват кунед:\n"
            f"🔗 `{ref_link}`",
            parse_mode="Markdown"
        )
        return

    # Кам кардани лимит
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
            contents=[
                uploaded_file, 
                "Determine the full feature length movie title (not TV series or short clip) from this video. Write ONLY the official movie title in Russian."
            ]
        )
        movie_name = response.text.strip()
        client.files.delete(name=uploaded_file.name)
        
        encoded_name = urllib.parse.quote(movie_name)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="▶️ Тамошои филми пурра (YouTube)", url=f"https://www.youtube.com/results?search_query=фильм+{encoded_name}+смотреть+полностью")],
            [InlineKeyboardButton(text="🌐 Ҷустуҷӯ дар Google", url=f"https://www.google.com/search?q=смотреть+фильм+{encoded_name}+в+хорошем+качестве")]
        ])
        
        await status_msg.edit_text(f"🎬 Номи филм:\n\n{movie_name}", reply_markup=keyboard)
        
    except Exception as e:
        await status_msg.edit_text(f"❌ Хатогӣ ҳангоми коркард: {e}")
    finally:
        if os.path.exists(video_path):
            os.remove(video_path)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
