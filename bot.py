import os
import sys
import json
import asyncio
import logging
import subprocess
import urllib.parse
from datetime import date

# ─── АВТО-СКАЧАТИ КИТОБХОНАИ YT-DLP ───
try:
    import yt_dlp
except ImportError:
    print("⏳ Китобхонаи 'yt-dlp' пайдо нашуд. Насбкунии худкор рафта истодааст...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp"])
    import yt_dlp
    print("✅ 'yt-dlp' бомуваффақият насб шуд!")

from google import genai
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

logging.basicConfig(level=logging.INFO)

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

# ─── 🌐 МАТНҲО БЕ РАМЗҲОИ ** ───
TEXTS = {
    "tg": {
        "welcome": (
            "Салом! 🎬 Ман боти Filmyob мебошам.\n\n"
            "🛠 Ман чӣ кор карда метавонам?\n"
            "Ман ба шумо барои ёфтани номи пӯрраи филмҳо (аз ҷумла филмҳо ва сериалҳои тоҷикӣ) кумак мекунам!\n\n"
            "Шумо метавонед ба ман:\n"
            "1️⃣ Порчаи видео (файли видео)-ро фиристед.\n"
            "2️⃣ Линки порчаи видеоро аз Instagram, YouTube, TikTok фиристед.\n\n"
            "Ман ба шумо маълумоти пурра, рейтинг, давомнокӣ ва линки тамошоро медиҳам! 🚀\n\n"
            "👇 Порчаи видео ё линки онро фиристед!"
        ),
        "btn_profile": "📊 Ҳисоби ман",
        "btn_rules": "📜 Қоидаҳо ва Линки рефералӣ",
        "btn_lang": "🌐 Забон / Язык / Language",
        "select_lang": "🌐 Лутфан аввал забонро интихоб кунед / Пожалуйста, выберите язык:",
        "lang_set": "✅ Забон интихоб шуд!",
        "sub_req": "⚠️ Барои истифодаи бот, аввал ба канали мо аъзо шавед!",
        "btn_sub": "📢 Аъзо шудан ба канал",
        "btn_check_sub": "✅ Аъзо шудам",
        "sub_ok": "✅ Тасдиқ шуд! /start-ро пахш кунед.",
        "sub_fail": "❌ Шумо ҳанӯз аъзо нашудаед!",
        "video_big": "⚠️ Ҳаҷми видео аз 19 МБ зиёд аст!",
        "limit_end": "🛑 Лимити имрӯза тамом шуд! (3/3)\n\n🎁 Барои +1 видео, дӯстонро даъват кунед:\n{ref_link}",
        "processing": "📥 Видео қабул шуд. Таҳлил ва ҷустуҷӯи филм рафта истодааст...",
        "downloading_link": "🔗 Линки видео қабул шуд, дар ҳоли боргирӣ...",
        "not_a_movie": "❌ Ин филм нест!\n\nВидеои фиристодашуда парча аз филм ё сериали бадеӣ нест.",
        "watch_tg": "🇹🇯 Тамошо (Забони Тоҷикӣ)",
        "watch_ru": "🇷🇺 Тамошо (Забони Русӣ)",
        "profile": "👤 Профили шумо: {name}{admin_note}\n🆔 ID: {user_id}\n📅 Лимити имрӯза: {daily} аз 3\n🎁 Бонусҳо: {bonus}\n👥 Дӯстон: {refs}",
        "rules_ref": "📜 ҚОИДАҲО:\n1️⃣ Видео ё линки Instagram/YouTube-ро фиристед.\n2️⃣ Лимити рӯзона: 3 видео.\n\n🔗 Линки рефералӣ:\n{ref_link}",
        "link_error": "❌ Хатогӣ ҳангоми боркашии линк. Лутфан линки дурустро фиристед."
    },
    "ru": {
        "welcome": (
            "Привет! 🎬 Я бот Filmyob.\n\n"
            "🛠 Что я умею?\n"
            "Я помогу найти полное название фильма (включая таджикские фильмы и сериалы)!\n\n"
            "Вы можете отправить мне:\n"
            "1️⃣ Отрывок видео (файл).\n"
            "2️⃣ Ссылку на видео из Instagram, YouTube, TikTok.\n\n"
            "Я предоставлю подробное описание, рейтинг, длительность и ссылки для просмотра! 🚀\n\n"
            "👇 Отправьте видео или ссылку!"
        ),
        "btn_profile": "📊 Мой профиль",
        "btn_rules": "📜 Правила и Рефералка",
        "btn_lang": "🌐 Забон / Язык / Language",
        "select_lang": "🌐 Пожалуйста, выберите язык / Лутфан забонро интихоб кунед:",
        "lang_set": "✅ Язык выбран!",
        "sub_req": "⚠️ Для использования бота подпишитесь на наш канал!",
        "btn_sub": "📢 Подписаться на канал",
        "btn_check_sub": "✅ Я подписался",
        "sub_ok": "✅ Подтверждено! Нажмите /start.",
        "sub_fail": "❌ Вы еще не подписались!",
        "video_big": "⚠️ Размер видео превышает 19 МБ!",
        "limit_end": "🛑 Дневной лимит исчерпан! (3/3)\n\n🎁 Для +1 видео приглашайте друзей:\n{ref_link}",
        "processing": "📥 Видео получено. Идет анализ и поиск фильма...",
        "downloading_link": "🔗 Ссылка получена, скачиваем видео...",
        "not_a_movie": "❌ Это не фильм!\n\nОтправленное видео не является отрывком из фильма или сериала.",
        "watch_tg": "🇹🇯 Смотреть (Таджикский язык)",
        "watch_ru": "🇷🇺 Смотреть (Русский язык)",
        "profile": "👤 Ваш профиль: {name}{admin_note}\n🆔 ID: {user_id}\n📅 Лимит на сегодня: {daily} из 3\n🎁 Бонусы: {bonus}\n👥 Друзья: {refs}",
        "rules_ref": "📜 ПРАВИЛА:\n1️⃣ Отправьте видео или ссылку Instagram/YouTube.\n2️⃣ Лимит: 3 видео в день.\n\n🔗 Реферальная ссылка:\n{ref_link}",
        "link_error": "❌ Ошибка при скачивании по ссылке. Проверьте ссылку."
    },
    "en": {
        "welcome": (
            "Hello! 🎬 I am Filmyob bot.\n\n"
            "🛠 What can I do?\n"
            "I will help you find full movie titles (including Tajik movies and series)!\n\n"
            "You can send me:\n"
            "1️⃣ A video clip file.\n"
            "2️⃣ A video link from Instagram, YouTube, TikTok.\n\n"
            "I will give you movie info, rating, duration, and watch links! 🚀\n\n"
            "👇 Send a video clip or link below!"
        ),
        "btn_profile": "📊 My Profile",
        "btn_rules": "📜 Rules & Referral",
        "btn_lang": "🌐 Забон / Язык / Language",
        "select_lang": "🌐 Please select your language:",
        "lang_set": "✅ Language set!",
        "sub_req": "⚠️ Please subscribe to our channel first!",
        "btn_sub": "📢 Subscribe to channel",
        "btn_check_sub": "✅ I subscribed",
        "sub_ok": "✅ Verified! Press /start.",
        "sub_fail": "❌ You haven't subscribed yet!",
        "video_big": "⚠️ Video exceeds 19 MB!",
        "limit_end": "🛑 Daily limit reached! (3/3)\n\n🎁 Invite friends for +1 bonus:\n{ref_link}",
        "processing": "📥 Video received. Analyzing and searching movie...",
        "downloading_link": "🔗 Link received, downloading video...",
        "not_a_movie": "❌ This is not a movie!\n\nThe sent video is not a clip from a movie or TV series.",
        "watch_tg": "🇹🇯 Watch in Tajik",
        "watch_ru": "🇷🇺 Watch in Russian",
        "profile": "👤 Your Profile: {name}{admin_note}\n🆔 ID: {user_id}\n📅 Today limit: {daily} of 3\n🎁 Bonuses: {bonus}\n👥 Friends: {refs}",
        "rules_ref": "📜 RULES:\n1️⃣ Send a video or Instagram/YouTube link.\n2️⃣ Limit: 3 videos daily.\n\n🔗 Referral Link:\n{ref_link}",
        "link_error": "❌ Failed to download video from link."
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

# ─── БОРГИРИИ ВИДЕО АЗ ЛИНК ───
async def download_video_from_url(url: str, output_path: str) -> bool:
    ydl_opts = {
        'format': 'mp4[filesize<20M]/best[filesize<20M]/best',
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

# ─── КӮШИШИ ДУБОРА БАРОИ ПЕШГИРИИ ХАТОГИИ 503 ───
async def generate_with_retry(uploaded_file, prompt, status_msg):
    for attempt in range(1, 4):
        try:
            return client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[uploaded_file, prompt]
            )
        except Exception as e:
            if ("503" in str(e) or "UNAVAILABLE" in str(e)) and attempt < 3:
                await asyncio.sleep(attempt * 3)
            else:
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

# ─── ИНТИХОБИ АВВАЛИНИ ЗАБОН ───
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

# ─── ИВАЗ КАРДАНИ ЗАБОН ───
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

# ─── МЕНЮҲОИ ДИГАР ───
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

# ─── КОРКАРДИ ВИДЕО ВА ТАҲЛИЛИ ФИЛМ ───
async def process_video_file(video_path: str, message: types.Message, status_msg: types.Message):
    user_id = str(message.from_user.id)
    lang = get_lang(user_id)
    
    try:
        uploaded_file = client.files.upload(file=video_path)
        while uploaded_file.state.name == "PROCESSING":
            await asyncio.sleep(2)
            uploaded_file = client.files.get(name=uploaded_file.name)

        prompt = (
            f"Analyze this video clip carefully. Check if it is from a feature movie, TV series, or Tajik cinema/series. "
            f"Do not use markdown bold formatting like asterisks. "
            f"If it is NOT a movie or drama series, reply EXACTLY: NOT_A_MOVIE. "
            f"If it IS a movie or series, provide details in language code '{lang}':\n"
            f"1. Full Movie Title\n"
            f"2. Duration\n"
            f"3. Rating\n"
            f"4. Main Actors\n"
            f"5. Short description\n\n"
            f"Format response like this without markdown symbols:\n"
            f"🎬 Номи филм: [Title]\n"
            f"⏱ Давомнокӣ: [Duration]\n"
            f"⭐ Рейтинг: [Rating]\n"
            f"🎭 Актёрон: [Actors]\n"
            f"📝 Мазмун: [Description]"
        )

        response = await generate_with_retry(uploaded_file, prompt, status_msg)
        result = response.text.strip().replace("*", "")
        client.files.delete(name=uploaded_file.name)

        if "NOT_A_MOVIE" in result or len(result) < 5:
            await status_msg.edit_text(TEXTS[lang]["not_a_movie"])
            return

        first_line = result.split("\n")[0]
        clean_title = first_line.replace("🎬 Номи филм:", "").replace("🎬 Название фильма:", "").replace("🎬 Movie Title:", "").strip()
        enc_title = urllib.parse.quote(clean_title if clean_title else "Movie")

        watch_tg_url = f"https://www.google.com/search?q={enc_title}+ба+забони+точики+تماша+филм"
        watch_ru_url = f"https://yandex.ru/search/?text=смотреть+фильм+{enc_title}+онлайн+бесплатно"

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=TEXTS[lang]["watch_tg"], url=watch_tg_url)],
            [InlineKeyboardButton(text=TEXTS[lang]["watch_ru"], url=watch_ru_url)]
        ])

        await status_msg.edit_text(result, reply_markup=keyboard)
    except Exception as e:
        await status_msg.edit_text(f"❌ Хатогӣ: {e}")

# Қабули файлҳои видео
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
    if os.path.exists(video_path): os.remove(video_path)

# Қабули линкҳо
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

    await status_msg.edit_text(TEXTS[lang]["processing"])
    await process_video_file(video_path, message, status_msg)
    if os.path.exists(video_path): os.remove(video_path)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
