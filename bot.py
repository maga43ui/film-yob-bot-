import os
import asyncio
import logging
import urllib.parse
from google import genai
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

logging.basicConfig(level=logging.INFO)

# 🔑 Токен ва номи бот
TELEGRAM_TOKEN = "8949334224:AAEip9Lbdxd2YFwS_rNNNls2vxaN6qkvfDc"
BOT_USERNAME = "@Filmyob_bot"

# 📢 Канали шумо ва API Key
CHANNEL_USERNAME = "@filmyob_channel"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

TEMP_DIR = "temp_videos"
os.makedirs(TEMP_DIR, exist_ok=True)

# Функсияи тафтиши аъзошавӣ ба канал
async def check_sub(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in ["creator", "administrator", "member"]
    except Exception as e:
        logging.error(f"Хатогии тафтиши аъзошавӣ: {e}")
        return True

@dp.message(CommandStart())
async def start_cmd(message: types.Message):
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

    await message.answer(
        f"Салом {message.from_user.first_name}! 🎬\n\n"
        f"Ман боти {BOT_USERNAME} ҳастам.\n"
        f"Парчаи видеоиро фиристед (аз 2 то 20 сония), то номи филмро пайдо кунам!"
    )

@dp.callback_query(F.data == "check_subscription")
async def check_sub_callback(call: types.CallbackQuery):
    if await check_sub(call.from_user.id):
        await call.message.delete()
        await call.message.answer("✅ **Раҳмат! Аъзошавӣ тасдиқ шуд.**\n\nИнҷо парчаи видеоиро фиристед!")
    else:
        await call.answer("❌ Шумо ҳанӯз ба канал аъзо нашудаед!", show_alert=True)

@dp.message(F.video | F.video_note)
async def handle_video(message: types.Message):
    is_subbed = await check_sub(message.from_user.id)
    if not is_subbed:
        await start_cmd(message)
        return

    status_msg = await message.answer("📥 Видео қабул шуд. Таҳлил рафта истодааст...")
    
    video_obj = message.video or message.video_note
    file_info = await bot.get_file(video_obj.file_id)
    video_path = os.path.join(TEMP_DIR, f"{message.from_user.id}.mp4")
    
    await bot.download_file(file_info.file_path, destination=video_path)
    
    try:
        uploaded_file = client.files.upload(file=video_path)
        
        while uploaded_file.state.name == "PROCESSING":
            await asyncio.sleep(2)
            uploaded_file = client.files.get(name=uploaded_file.name)

        # ✅ Қавсҳо аниқ ва дуруст карда шуданд
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
        
        await status_msg.edit_text(
            f"🎬 Номи филм:\n\n{movie_name}", 
            reply_markup=keyboard
        )
        
    except Exception as e:
        await status_msg.edit_text(f"❌ Хатогӣ ҳангоми коркард: {e}")
    finally:
        if os.path.exists(video_path):
            os.remove(video_path)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
