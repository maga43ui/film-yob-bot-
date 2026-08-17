import os
import asyncio
import logging
import urllib.parse
from google import genai
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

logging.basicConfig(level=logging.INFO)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
CHANNEL_USERNAME = os.environ.get("CHANNEL_USERNAME", "@канали_шумо")

# Мизоҷи нави Gemini Client
client = genai.Client(api_key=GEMINI_API_KEY)

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

TEMP_DIR = "temp_videos"
os.makedirs(TEMP_DIR, exist_ok=True)

async def check_sub(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in ["creator", "administrator", "member"]
    except:
        return True

@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    await message.answer("Салом! Парчаи видеоро фиристед, то номи филмро гӯям.")

@dp.message(F.video | F.video_note)
async def handle_video(message: types.Message):
    status_msg = await message.answer("📥 Видео қабул шуд. Дар ҳоли таҳлил...")
    video_obj = message.video or message.video_note
    file_info = await bot.get_file(video_obj.file_id)
    video_path = os.path.join(TEMP_DIR, f"{message.from_user.id}.mp4")
    
    await bot.download_file(file_info.file_path, destination=video_path)
    
    try:
        # Боркунии видео бо SDK-и нав
        uploaded_file = client.files.upload(file=video_path)
        
        while uploaded_file.state.name == "PROCESSING":
            await asyncio.sleep(2)
            uploaded_file = client.files.get(name=uploaded_file.name)

        # Генерацияи ҷавоб бо модели gemini-2.5-flash
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[uploaded_file, "Напиши только название фильма из этого видео."]
        )
        movie_name = response.text.strip()
        
        # Пок кардани файли муваққатӣ аз Google
        client.files.delete(name=uploaded_file.name)
        
        encoded_name = urllib.parse.quote(movie_name)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="▶️ YouTube", url=f"https://www.youtube.com/results?search_query={encoded_name}+фильм")],
            [InlineKeyboardButton(text="🌐 Google", url=f"https://www.google.com/search?q=смотреть+{encoded_name}+онлайн")]
        ])
        
        await status_msg.edit_text(f"🎬 **Филм:** `{movie_name}`", reply_markup=keyboard, parse_mode="Markdown")
        
    except Exception as e:
        await status_msg.edit_text(f"❌ Хатогӣ: {e}")
    finally:
        if os.path.exists(video_path):
            os.remove(video_path)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
