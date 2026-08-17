import os
import asyncio
import logging
import urllib.parse
from google import genai
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

logging.basicConfig(level=logging.INFO)

# 🔑 Токени Telegram ва бот
TELEGRAM_TOKEN = "8949334224:AAEip9Lbdxd2YFwS_rNNNls2vxaN6qkvfDc"
BOT_USERNAME = "@Filmyob_bot"

# 🔑 Gemini API Key аз Railway Variables хонда мешавад
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
CHANNEL_USERNAME = os.environ.get("CHANNEL_USERNAME", "@канали_шумо")

client = genai.Client(api_key=GEMINI_API_KEY)
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

TEMP_DIR = "temp_videos"
os.makedirs(TEMP_DIR, exist_ok=True)

async def check_sub(user_id: int) -> bool:
    if CHANNEL_USERNAME == "@канали_шумо":
        return True
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in ["creator", "administrator", "member"]
    except:
        return True

@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    await message.answer(
        f"Салом {message.from_user.first_name}! 🎬\n\n"
        f"Ман боти {BOT_USERNAME} ҳастам.\n"
        f"Парчаи видеоиро фиристед (аз 2 то 20 сония), то номи филмро пайдо кунам!"
    )

@dp.message(F.video | F.video_note)
async def handle_video(message: types.Message):
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

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[uploaded_file, "Determine the movie title from this video. Write ONLY the title in Russian."]
        )
        movie_name = response.text.strip()
        
        client.files.delete(name=uploaded_file.name)
        
        encoded_name = urllib.parse.quote(movie_name)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="▶️ Тамошо дар YouTube", url=f"https://www.youtube.com/results?search_query={encoded_name}+фильм")],
            [InlineKeyboardButton(text="🌐 Ҷустуҷӯ дар Google", url=f"https://www.google.com/search?q=смотреть+{encoded_name}+онлайн")]
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
