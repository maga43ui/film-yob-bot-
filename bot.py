import os
import sys
import json
import asyncio
import logging
import subprocess
import urllib.parse
from datetime import date
import aiohttp

# ─── АВТО-СКАЧАТИ КИТОБХОНАИ YT-DLP ───
try:
    import yt_dlp
except ImportError:
    print("⏳ Китобхонаи 'yt-dlp' пайдо нашуд. Насбкунии худкор рафта истодааст...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp"])
    import yt_dlp
    print("✅ 'yt-dlp' бомуваффақият насб шуд!")

from google import genai
from google.genai import types as genai_types
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

logging.basicConfig(level=logging.INFO)
log = logging.getLogger('adverts')

# 🔑 Танзимот
TELEGRAM_TOKEN = "8949334224:AAEip9Lbdxd2YFwS_rNNNls2vxaN6qkvfDc"
ADMIN_ID = "8419536226"
BOT_USERNAME = "Filmyob_bot"
CHANNEL_USERNAME = "@filmyob_channel"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

TEMP_DIR = "temp_videos"
DATA_FILE = "users_data.json"
os.makedirs(TEMP_DIR, exist_ok=True)

# ─── GRAMADS РЕКЛАМА (ЛОГҲО ТАНҲО БА АДМИН МЕРАВАНД) ───
async def show_advert(user_id: int):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                'https://api.gramads.net/ad/SendPost',
                headers={
                    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1Nzk3NSIsImp0aSI6ImRjMzcxNjYzLWIxZDAtNDExMS04YzcxLTE4YjEyYmRhNDAyYSIsIm5hbWUiOiJGaWxtWW9iLmJvdCIsImJvdGlkIjoiMjIwNzMiLCJodHRwOi8vc2NoZW1hcy54bWxzb2FwLm9yZy93cy8yMDA1LzA1L2lkZW50aXR5L2NsYWltcy9uYW1laWRlbnRpZmllciI6IjU3OTc1IiwibmJmIjoxNzg3MjA2NzI5LCJleHAiOjE3ODc0MTU1MjksImlzcyI6IlN0dWdub3YiLCJhdWQiOiJVc2VycyJ9.MSACT2Z-ZIy6cqCNZcskdDSY2gpHZG8s64toWc01-2g',
                    'Content-Type': 'application/json',
                },
                json={'SendToChatId': str(user_id)},
            ) as response:
                response_text = await response.text()
                
                # МАТНИ ЛОГ БАРОИ АДМИН
                admin_log_message = (
                    f"⚙️ **GramAds API Log**\n"
                    f"👤 User ID: `{user_id}`\n"
                    f"📊 Status Code: `{response.status}`\n"
                    f"📄 Response Body:\n`{response_text}`"
                )
                
                # Фиристодани лог мустақиман ба ЛИЧКАИ АДМИН
                try:
                    await bot.send_message(chat_id=ADMIN_ID, text=admin_log_message, parse_mode="Markdown")
                except Exception as log_err:
                    print(f"Хатогӣ ҳангоми фиристодани лог ба админ: {log_err}")
                
                if not response.ok:
                    log.error(f'Gramads Error: {response_text}')
        except Exception as e:
            error_msg = f"⚠️ **GramAds Request Exception:**\n`{e}`"
            try:
                await bot.send_message(chat_id=ADMIN_ID, text=error_msg, parse_mode="Markdown")
            except:
                pass

# ─── 🌐 МАТНҲО ───
TEXTS = {
    "tg": {
        "welcome": (
            "Салом! 🎬 Ман боти Filmyob мебошам.\n\n"
            "🛠 Ман чӣ кор карда метавонам?\n"
            "Ман ба шумо барои ёфтани номи пураи филмҳо кумак мекунам!\n\n"
            "Шумо метавонед ба ман:\n"
            "1️⃣ Порчаи видео фиристед.\n"
            "2️⃣ Линки порчаи видеоро аз Instagram, YouTube, TikTok фиристед.\n\n"
            "👇 Порчаи видео ё линки онро фиристед!"
        ),
        "btn_profile": "📊 Ҳисоби ман",
        "btn_rules": "📜 Қоидаҳо ва Линки рефералӣ",
        "btn_lang": "🌐 Забон / Язык / Language",
        "select_lang": "🌐 Лутфан аввал забонро интихоб кунед:",
        "lang_set": "✅ Забон интихоб шуд!",
        "sub_req": "⚠️ Барои истифодаи бот, аввал ба канали мо аъзо шавед!",
        "btn_sub": "📢 Аъзо шудан ба канал",
        "btn_check_sub": "✅ Аъзо шудам",
        "video_big": "⚠️ Ҳаҷми видео аз 19 МБ зиёд аст!",
        "limit_end": "🛑 Лимити имрӯза тамом шуд! (3/3)\n\n🎁 Барои +1 видео, дӯстонро даъват кунед:\n{ref_link}",
        "processing": "📥 Видео қабул шуд. Таҳлил рафта истодааст...",
        "downloading_link": "🔗 Линки видео қабул шуд, дар ҳоли боргирӣ...",
        "not_a_movie": "❌ Ин филм ё сериали шинохташуда нест!",
        "not_in_server": "😔 Ман дар серверам ин филмро надорам.",
        "watch_tg": "🇹🇯 Тамошо дар YouTube / Google",
        "watch_ru": "🇷🇺 Тамошо дар Yandex",
        "profile": "👤 Профили шумо: {name}{admin_note}\n🆔 ID: {user_id}\n📅 Лимити имрӯза: {daily} аз 3\n🎁 Бонусҳо: {bonus}\n👥 Дӯстон: {refs}",
        "rules_ref": "📜 ҚОИДАҲО:\n1️⃣ Видео ё линк фиристед.\n2️⃣ Лимити рӯзона: 3 видео.\n\n🔗 Линки рефералӣ:\n{ref_link}",
        "link_error": "❌ Хатогӣ ҳангоми боркашии линк. Лутфан линки дурустро фиристед."
    },
    "ru": {
        "welcome": "Привет! 🎬 Я бот Filmyob.",
        "btn_profile": "📊 Мой профиль",
        "btn_rules": "📜 Правила и Рефералка",
        "btn_lang": "🌐 Забон / Язык / Language",
        "select_lang": "🌐 Пожалуйста, выберите язык:",
        "lang_set": "✅ Язык выбран!",
        "sub_req": "⚠️ Для использования бота подпишитесь на наш канал!",
        "btn_sub": "📢 Подписаться на канал",
        "btn_check_sub": "✅ Я подписался",
        "video_big": "⚠️ Размер видео превышает 19 МБ!",
        "limit_end": "🛑 Дневной лимит исчерпан!",
        "processing": "📥 Идет анализ фильма...",
        "downloading_link": "🔗 Скачиваем видео...",
        "not_a_movie": "❌ Это не фильм и не сериал!",
        "not_in_server": "😔 У меня на сервере нет этого фильма.",
        "watch_tg": "🇹🇯 Смотреть в YouTube / Google",
        "watch_ru": "🇷🇺 Смотреть в Yandex",
        "profile": "👤 Ваш профиль: {name}{admin_note}\n🆔 ID: {user_id}\n📅 Лимит: {daily} из 3\n🎁 Бонусы: {bonus}\n👥 Друзья: {refs}",
        "rules_ref": "📜 ПРАВИЛА:\n1️⃣ Отправьте видео или ссылку.\n\n🔗 Ссылка:\n{ref_link}",
        "link_error": "❌ Ошибка при скачивании."
    },
    "en": {
        "welcome": "Hello! 🎬 I am Filmyob bot.",
        "btn_profile": "📊 My Profile",
        "btn_rules": "📜 Rules & Referral",
        "btn_lang": "🌐 Language",
        "select_lang": "🌐 Select language:",
        "lang_set": "✅ Language set!",
        "sub_req": "⚠️ Please subscribe to channel!",
        "btn_sub": "📢 Subscribe",
        "btn_check_sub": "✅ Check",
        "video_big": "⚠️ Video exceeds 19 MB!",
        "limit_end": "🛑 Limit reached!",
        "processing": "📥 Analyzing video...",
        "downloading_link": "🔗 Downloading...",
        "not_a_movie": "❌ Not a movie!",
        "not_in_server": "😔 I do not have this movie on my server.",
        "watch_tg": "🇹🇯 Watch on YouTube / Google",
        "watch_ru": "🇷🇺 Watch on Yandex",
        "profile": "👤 Profile: {name}\n🆔 ID: {user_id}\n📅 Limit: {daily}\n🎁 Bonus: {bonus}\n👥 Refs: {refs}",
        "rules_ref": "📜 RULES:\nSend video/link.\n\nLink:\n{ref_link}",
        "link_error": "❌ Download failed."
    }
}

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
        data[user_id] = {
            "referrals": [], 
            "bonus_videos": 0, 
            "daily_date": today, 
            "daily_count": 0,
            "lang": None
        }
    else:
        if data[user_id].get("daily_date") != today:
            data[user_id]["daily_date"] = today
            data[user_id]["daily_count"] = 0
    save_data(data)
    return data

def get_lang(user_id: str) -> str:
    data = load_data()
    return data.get(str(user_id), {}).get("lang", "tg")

def check_and_use_limit(user_id: str) -> bool:
    if user_id == ADMIN_ID:
        return True
    all_data = load_data()
    user = all_data.get(user_id)
    if not user:
        return False

    if user["daily_count"] < 3:
        user["daily_count"] += 1
        save_data(all_data)
        return True
    elif user["bonus_videos"] > 0:
        user["bonus_videos"] -= 1
        save_data(all_data)
        return True
    return False

def get_main_keyboard(lang: str):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=TEXTS[lang]["btn_profile"])],
            [KeyboardButton(text=TEXTS[lang]["btn_rules"])],
            [KeyboardButton(text=TEXTS[lang]["btn_lang"])]
        ],
        resize_keyboard=True
    )

async def check_sub(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in ["creator", "administrator", "member"]
    except:
        return True

# ─── БОРГИРИИ ТЕЗКОРИ ВИДЕО АЗ ЛИНК ───
async def download_video_from_url(url: str, output_path: str) -> bool:
    ydl_opts = {
        'format': 'b[filesize<15M]/worst[ext=mp4]/w',
        'outtmpl': output_path,
        'quiet': True,
        'no_warnings': True,
        'max_filesize': 20 * 1024 * 1024
    }
    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).download([url]))
        return os.path.exists(output_path)
    except Exception as e:
        logging.error(f"Download error: {e}")
        return False

# ─── МОДЕЛИ GEMINI 3.6 ───
async def generate_with_retry(uploaded_file, prompt):
    try:
        return client.models.generate_content(
            model='gemini-3.6-flash',
            contents=[uploaded_file, prompt],
            config=genai_types.GenerateContentConfig(
                temperature=0.0
            )
        )
    except Exception as e:
        if "503" in str(e) or "UNAVAILABLE" in str(e):
            await asyncio.sleep(2)
            return client.models.generate_content(
                model='gemini-3.6-flash',
                contents=[uploaded_file, prompt],
                config=genai_types.GenerateContentConfig(
                    temperature=0.0
                )
            )
        raise e

# ─── COMMAND /START ───
@dp.message(CommandStart())
async def start_cmd(message: types.Message, command: CommandObject):
    user_id = str(message.from_user.id)
    all_data = get_user_data(user_id)
    u_data = all_data[user_id]

    ref_id = command.args
    if ref_id and ref_id != user_id and ref_id in all_data:
        if user_id not in all_data[ref_id]["referrals"]:
            all_data[ref_id]["referrals"].append(user_id)
            if len(all_data[ref_id]["referrals"]) % 2 == 0:
                all_data[ref_id]["bonus_videos"] += 1
            save_data(all_data)

    if not u_data.get("lang"):
        lang_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🇹🇯 Тоҷикӣ", callback_data="init_lang_tg")],
            [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="init_lang_ru")],
            [InlineKeyboardButton(text="🇬🇧 English", callback_data="init_lang_en")]
        ])
        await message.answer(TEXTS["tg"]["select_lang"], reply_markup=lang_kb)
        return

    lang = u_data["lang"]

    if not await check_sub(message.from_user.id):
        sub_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=TEXTS[lang]["btn_sub"], url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")],
            [InlineKeyboardButton(text=TEXTS[lang]["btn_check_sub"], callback_data="check_subscription")]
        ])
        await message.answer(TEXTS[lang]["sub_req"], reply_markup=sub_kb)
        return

    await message.answer(TEXTS[lang]["welcome"], reply_markup=get_main_keyboard(lang))

@dp.callback_query(F.data.startswith("init_lang_"))
async def init_lang_callback(call: types.CallbackQuery):
    selected_lang = call.data.split("_")[-1]
    user_id = str(call.from_user.id)
    all_data = load_data()
    if user_id in all_data:
        all_data[user_id]["lang"] = selected_lang
        save_data(all_data)
    await call.message.delete()
    await call.message.answer(TEXTS[selected_lang]["welcome"], reply_markup=get_main_keyboard(selected_lang))

@dp.message(F.text.contains("Забон") | F.text.contains("Язык") | F.text.contains("Language"))
async def lang_menu_cmd(message: types.Message):
    lang = get_lang(str(message.from_user.id))
    lang_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇹🇯 Тоҷикӣ", callback_data="set_lang_tg")],
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="set_lang_ru")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="set_lang_en")]
    ])
    await message.answer(TEXTS[lang]["select_lang"], reply_markup=lang_kb)

@dp.callback_query(F.data.startswith("set_lang_"))
async def set_lang_callback(call: types.CallbackQuery):
    selected_lang = call.data.split("_")[-1]
    user_id = str(call.from_user.id)
    all_data = load_data()
    all_data[user_id]["lang"] = selected_lang
    save_data(all_data)
    await call.message.delete()
    await call.message.answer(TEXTS[selected_lang]["lang_set"], reply_markup=get_main_keyboard(selected_lang))

@dp.message(F.text.in_({"📊 Ҳисоби ман", "📊 Мой профиль", "📊 My Profile"}))
async def profile_cmd(message: types.Message):
    user_id = str(message.from_user.id)
    u_data = get_user_data(user_id)[user_id]
    lang = u_data.get("lang", "tg")
    daily_left = max(0, 3 - u_data["daily_count"])
    admin_note = " (👑 Админ)" if user_id == ADMIN_ID else ""
    text = TEXTS[lang]["profile"].format(
        name=message.from_user.first_name, admin_note=admin_note,
        user_id=user_id, daily=daily_left, bonus=u_data["bonus_videos"], refs=len(u_data["referrals"])
    )
    await message.answer(text)

@dp.message(F.text.in_({"📜 Қоидаҳо ва Линки рефералӣ", "📜 Правила и Рефералка", "📜 Rules & Referral"}))
async def info_cmd(message: types.Message):
    user_id = str(message.from_user.id)
    lang = get_lang(user_id)
    ref_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
    await message.answer(TEXTS[lang]["rules_ref"].format(ref_link=ref_link))

# ─── КОРКАРДИ ВИДЕО ВА ТАҲЛИЛ ───
async def process_video_file(video_path: str, message: types.Message, status_msg: types.Message):
    user_id = str(message.from_user.id)
    lang = get_lang(user_id)

    try:
        uploaded_file = client.files.upload(file=video_path)
        while uploaded_file.state.name == "PROCESSING":
            await asyncio.sleep(1)
            uploaded_file = client.files.get(name=uploaded_file.name)

        prompt = (
            f"You are an absolute factual AI expert in global and Tajik movies/TV series. "
            f"Analyze this video clip carefully.\n\n"
            f"CRITICAL STRICT RULES:\n"
            f"1. DO NOT GUESS OR HALLUCINATE AT ALL. NO ASSUMPTIONS.\n"
            f"2. You must be at least 90%-100% confident based on exact visual, facial, or scene match.\n"
            f"3. Check for Tajik series like 'Khusuri man', 'Nomus', 'Mardon', 'Zanho', 'Dar justujui haqiqat', or content from Zamonavi Media, Futuwwat, and Tajik film studios.\n"
            f"4. IF YOU DO NOT KNOW THE EXACT MOVIE OR ARE NOT 90% CONFIDENT, REPLY ONLY WITH THIS EXACT WORD: NOT_FOUND\n"
            f"5. IF IT IS NOT A MOVIE OR DRAMA AT ALL, REPLY ONLY WITH THIS EXACT WORD: NOT_A_MOVIE\n\n"
            f"If you are 90%-100% certain of the movie title, provide details in language code '{lang}':\n"
            f"Do NOT use markdown bold formatting like asterisks (*).\n"
            f"1. Full Title\n"
            f"2. Duration\n"
            f"3. Rating\n"
            f"4. Main Actors\n"
            f"5. Short plot summary\n\n"
            f"Format response strictly as:\n"
            f"🎬 Номи филм: [Title]\n"
            f"⏱ Давомнокӣ: [Duration]\n"
            f"⭐ Рейтинг: [Rating]\n"
            f"🎭 Актёрон: [Actors]\n"
            f"📝 Мазмун: [Description]"
        )

        response = await generate_with_retry(uploaded_file, prompt)
        result = response.text.strip().replace("*", "")
        client.files.delete(name=uploaded_file.name)

        if "NOT_A_MOVIE" in result:
            await status_msg.edit_text(TEXTS[lang]["not_a_movie"])
            return

        if "NOT_FOUND" in result or len(result) < 5:
            await status_msg.edit_text(TEXTS[lang]["not_in_server"])
            return

        first_line = result.split("\n")[0]
        clean_title = first_line.replace("🎬 Номи филм:", "").replace("🎬 Название фильма:", "").replace("🎬 Movie Title:", "").strip()
        enc_title = urllib.parse.quote(clean_title if clean_title else "Хусури ман")

        watch_tg_url = f"https://www.youtube.com/results?search_query={enc_title}"
        watch_ru_url = f"https://yandex.ru/search/?text=смотреть+сериал+{enc_title}+онлайн"

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=TEXTS[lang]["watch_tg"], url=watch_tg_url)],
            [InlineKeyboardButton(text=TEXTS[lang]["watch_ru"], url=watch_ru_url)]
        ])

        await status_msg.edit_text(result, reply_markup=keyboard)

        # 📢 Фиристодани реклама ба корбар пас аз гирифтани натиҷа
        await show_advert(int(user_id))

    except Exception as e:
        await status_msg.edit_text(f"❌ Хатогӣ: {e}")

# Қабули видеоҳо
@dp.message(F.video | F.video_note)
async def handle_video(message: types.Message):
    user_id = str(message.from_user.id)
    lang = get_lang(user_id)

    if not check_and_use_limit(user_id):
        ref_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
        await message.answer(TEXTS[lang]["limit_end"].format(ref_link=ref_link))
        return

    video_obj = message.video or message.video_note
    if video_obj.file_size > 19 * 1024 * 1024:
        await message.answer(TEXTS[lang]["video_big"])
        return

    status_msg = await message.answer(TEXTS[lang]["processing"])
    file_info = await bot.get_file(video_obj.file_id)
    video_path = os.path.join(TEMP_DIR, f"{user_id}.mp4")
    await bot.download_file(file_info.file_path, destination=video_path)

    await process_video_file(video_path, message, status_msg)
    if os.path.exists(video_path): 
        os.remove(video_path)

# Қабули линкҳо (Ислоҳшуда)
@dp.message(F.text.startswith("http://") | F.text.startswith("https://"))
async def handle_link(message: types.Message):
    user_id = str(message.from_user.id)
    lang = get_lang(user_id)

    if not check_and_use_limit(user_id):
        ref_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
        await message.answer(TEXTS[lang]["limit_end"].format(ref_link=ref_link))
        return

    status_msg = await message.answer(TEXTS[lang]["downloading_link"])
    video_path = os.path.join(TEMP_DIR, f"{user_id}_link.mp4")

    success = await download_video_from_url(message.text.strip(), video_path)
    if not success:
        await status_msg.edit_text(TEXTS[lang]["link_error"])
        return

    await process_video_file(video_path, message, status_msg)
    if os.path.exists(video_path): 
        os.remove(video_path)

# ─── ИШҒОЛ КАРДАНИ ПОЛИНГ ───
async def main():
    print("🚀 Бот бомуваффақият ба кор даромад...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
