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

# ─── 🌐 ЛУҒАТИ МАТНҲО (3 ЗАБОН) ───
TEXTS = {
    "tg": {
        "welcome": "Салом {name}! 🎬\n\n📜 **ҚОИДАҲОИ БОТ:**\n1️⃣ Ҳаҷми видео: то **19 МБ**.\n2️⃣ Лимити рӯзона: **3 видео**.\n3️⃣ **Бонус:** Барои 2 дӯсти даъваткарда, **+1 видео** мегиред!\n\n👇 Видеоро фиристед ё аз меню истифода баред!",
        "btn_profile": "📊 Ҳисоби ман",
        "btn_rules": "📜 Қоидаҳо ва Линки рефералӣ",
        "btn_lang": "🌐 Забон / Язык / Language",
        "select_lang": "Лутфан забонро интихоб кунед:",
        "lang_set": "✅ Забон ба Тоҷикӣ иваз карда шуд!",
        "sub_req": "⚠️ Барои истифодаи бот, аввал ба канали мо аъзо шавед!",
        "btn_sub": "📢 Аъзо шудан ба канал",
        "btn_check_sub": "✅ Аъзо шудам",
        "sub_ok": "✅ Тасдиқ шуд! Боз як бор /start-ро пахш кунед.",
        "sub_fail": "❌ Шумо ҳанӯз аъзо нашудаед!",
        "video_big": "⚠️ **Видео пок шуд!** Ҳаҷм аз 19 МБ зиёд аст.",
        "limit_end": "🛑 **Лимити имрӯза тамом шуд!**\n\n🎁 Барои +1 видео, дӯстонро даъват кунед:\n`{ref_link}`",
        "processing": "📥 Видео қабул шуд. Таҳлил рафта истодааст...",
        "movie_title": "🎬 Номи филм:\n\n{title}",
        "profile": "👤 **Профили шумо:** {name}{admin_note}\n🆔 **ID:** `{user_id}`\n\n📅 **Лимити имрӯза:** {daily} аз 3 видео\n🎁 **Видеоҳои бонусӣ:** {bonus} адад\n👥 **Дӯстони даъватшуда:** {refs} нафар",
        "rules_ref": "📜 **ҚОИДАҲОИ БОТ:**\n1️⃣ Ҳаҷми видео: то **19 МБ**.\n2️⃣ Лимити рӯзона: **3 видео**.\n3️⃣ Барои 2 дӯст = **+1 видеои бонусӣ**.\n\n🔗 **Линки рефералии шумо:**\n`{ref_link}`",
        "restart_msg": "🔄 **Бот навсозӣ шуд!**\n\nЛутфан барои идомаи кор /start-ро пахш кунед.",
        "bonus_notify": "🎉 **Табрик!** Шумо 2 дӯстатонро даъват кардед ва +1 видеои бонусӣ гирифтед!",
        "send_only_video": "ℹ️ Лутфан танҳо **пачаи видео** (кино)-ро фиристед ё тугмаҳои менюро истифода баред."
    },
    "ru": {
        "welcome": "Привет, {name}! 🎬\n\n📜 **ПРАВИЛА БОТА:**\n1️⃣ Размер видео: до **19 МБ**.\n2️⃣ Дневной лимит: **3 видео**.\n3️⃣ **Бонус:** За 2 приглашенных друзей **+1 видео**!\n\n👇 Отправьте видео или используйте меню!",
        "btn_profile": "📊 Мой профиль",
        "btn_rules": "📜 Правила и Рефералка",
        "btn_lang": "🌐 Забон / Язык / Language",
        "select_lang": "Пожалуйста, выберите язык:",
        "lang_set": "✅ Язык успешно изменен на Русский!",
        "sub_req": "⚠️ Для использования бота подпишитесь на наш канал!",
        "btn_sub": "📢 Подписаться на канал",
        "btn_check_sub": "✅ Я подписался",
        "sub_ok": "✅ Подписка подтверждена! Нажмите /start еще раз.",
        "sub_fail": "❌ Вы еще не подписались!",
        "video_big": "⚠️ **Видео удалено!** Размер превышает 19 МБ.",
        "limit_end": "🛑 **Дневной лимит исчерпан!**\n\n🎁 Для получения +1 видео приглашайте друзей:\n`{ref_link}`",
        "processing": "📥 Видео получено. Идет анализ...",
        "movie_title": "🎬 Название фильма:\n\n{title}",
        "profile": "👤 **Ваш профиль:** {name}{admin_note}\n🆔 **ID:** `{user_id}`\n\n📅 **Лимит на сегодня:** {daily} из 3 видео\n🎁 **Бонусные видео:** {bonus} шт.\n👥 **Приглашено друзей:** {refs} чел.",
        "rules_ref": "📜 **ПРАВИЛА БОТА:**\n1️⃣ Размер видео: до **19 МБ**.\n2️⃣ Дневной лимит: **3 видео**.\n3️⃣ За 2 друзей = **+1 бонусное видео**.\n\n🔗 **Ваша реферальная ссылка:**\n`{ref_link}`",
        "restart_msg": "🔄 **Бот обновлен!**\n\nПожалуйста, нажмите /start для продолжения.",
        "bonus_notify": "🎉 **Поздравляем!** Вы пригласили 2 друзей и получили +1 бонусное видео!",
        "send_only_video": "ℹ️ Пожалуйста, отправляйте только **видео отрывки** или используйте кнопки меню."
    },
    "en": {
        "welcome": "Hello {name}! 🎬\n\n📜 **BOT RULES:**\n1️⃣ Video size: up to **19 MB**.\n2️⃣ Daily limit: **3 videos**.\n3️⃣ **Bonus:** Get **+1 video** for every 2 invited friends!\n\n👇 Send a video or use the menu below!",
        "btn_profile": "📊 My Profile",
        "btn_rules": "📜 Rules & Referral",
        "btn_lang": "🌐 Забон / Язык / Language",
        "select_lang": "Please select your language:",
        "lang_set": "✅ Language changed to English!",
        "sub_req": "⚠️ To use the bot, please subscribe to our channel first!",
        "btn_sub": "📢 Subscribe to channel",
        "btn_check_sub": "✅ I subscribed",
        "sub_ok": "✅ Verified! Please press /start again.",
        "sub_fail": "❌ You haven't subscribed yet!",
        "video_big": "⚠️ **Video deleted!** Size exceeds 19 MB.",
        "limit_end": "🛑 **Daily limit reached!**\n\n🎁 Invite friends to get +1 extra video:\n`{ref_link}`",
        "processing": "📥 Video received. Analyzing...",
        "movie_title": "🎬 Movie Title:\n\n{title}",
        "profile": "👤 **Your Profile:** {name}{admin_note}\n🆔 **ID:** `{user_id}`\n\n📅 **Today's limit:** {daily} of 3 videos\n🎁 **Bonus videos:** {bonus}\n👥 **Invited friends:** {refs}",
        "rules_ref": "📜 **BOT RULES:**\n1️⃣ Video size: up to **19 MB**.\n2️⃣ Daily limit: **3 videos**.\n3️⃣ Every 2 friends = **+1 bonus video**.\n\n🔗 **Your referral link:**\n`{ref_link}`",
        "restart_msg": "🔄 **Bot updated!**\n\nPlease press /start to continue.",
        "bonus_notify": "🎉 **Congratulations!** You invited 2 friends and received +1 bonus video!",
        "send_only_video": "ℹ️ Please send only **video clips** or use the menu buttons."
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
            "lang": "tg"  # Забони пешфарз - Тоҷикӣ
        }
    else:
        if "lang" not in data[user_id]:
            data[user_id]["lang"] = "tg"
        if data[user_id].get("daily_date") != today:
            data[user_id]["daily_date"] = today
            data[user_id]["daily_count"] = 0
    save_data(data)
    return data

def get_lang(user_id: str) -> str:
    data = load_data()
    return data.get(str(user_id), {}).get("lang", "tg")

# ─── МЕНЮИ АСОСӢ ───
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

# ─── ХАБАРДОР КАРДАНИ КОРБАРОН ВАҚТИ РӮШАН ШУДАНИ БОТ ───
async def notify_users_on_restart():
    data = load_data()
    start_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 /start", url=f"https://t.me/{BOT_USERNAME}?start=restart")]
    ])
    
    for user_id, u_info in data.items():
        lang = u_info.get("lang", "tg")
        try:
            await bot.send_message(
                chat_id=int(user_id), 
                text=TEXTS[lang]["restart_msg"], 
                reply_markup=start_kb, 
                parse_mode="Markdown"
            )
            await asyncio.sleep(0.05)
        except Exception:
            pass

# ─── 1. COMMAND /START ───
@dp.message(CommandStart())
async def start_cmd(message: types.Message, command: CommandObject):
    user_id = str(message.from_user.id)
    get_user_data(user_id)
    lang = get_lang(user_id)
    
    referrer_id = command.args
    if referrer_id and referrer_id != user_id and referrer_id != "restart":
        all_data = load_data()
        if referrer_id in all_data and user_id not in all_data[referrer_id]["referrals"]:
            all_data[referrer_id]["referrals"].append(user_id)
            if len(all_data[referrer_id]["referrals"]) % 2 == 0:
                all_data[referrer_id]["bonus_videos"] += 1
                ref_lang = all_data[referrer_id].get("lang", "tg")
                try: 
                    await bot.send_message(int(referrer_id), TEXTS[ref_lang]["bonus_notify"])
                except: 
                    pass
            save_data(all_data)

    if not await check_sub(message.from_user.id):
        sub_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=TEXTS[lang]["btn_sub"], url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")],
            [InlineKeyboardButton(text=TEXTS[lang]["btn_check_sub"], callback_data="check_subscription")]
        ])
        await message.answer(TEXTS[lang]["sub_req"], reply_markup=sub_kb)
        return

    welcome_text = TEXTS[lang]["welcome"].format(name=message.from_user.first_name)
    await message.answer(welcome_text, reply_markup=get_main_keyboard(lang), parse_mode="Markdown")

# ─── 2. CALLBACK ДАЪВАТИ КАНАЛ ───
@dp.callback_query(F.data == "check_subscription")
async def check_sub_callback(call: types.CallbackQuery):
    lang = get_lang(str(call.from_user.id))
    if await check_sub(call.from_user.id):
        await call.message.delete()
        await call.message.answer(TEXTS[lang]["sub_ok"])
    else:
        await call.answer(TEXTS[lang]["sub_fail"], show_alert=True)

# ─── 3. ИВАЗ КАРДАНИ ЗАБОН ───
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
    if user_id in all_data:
        all_data[user_id]["lang"] = selected_lang
        save_data(all_data)
        
    await call.message.delete()
    await call.message.answer(
        TEXTS[selected_lang]["lang_set"], 
        reply_markup=get_main_keyboard(selected_lang)
    )

# ─── 4. COMMAND /ADMIN ───
@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if str(message.from_user.id) != ADMIN_ID:
        return
    data = load_data()
    user_count = len(data)
    await message.answer(f"👑 **ПАНЕЛИ АДМИН**\n\n👥 Шумораи умумии корбарон: {user_count}")

# ─── 5. ТУГМАИ ПРОФИЛЬ ───
@dp.message(F.text.in_({"📊 Ҳисоби ман", "📊 Мой профиль", "📊 My Profile"}))
async def profile_cmd(message: types.Message):
    user_id = str(message.from_user.id)
    all_data = get_user_data(user_id)
    u_data = all_data[user_id]
    lang = u_data.get("lang", "tg")
    
    daily_left = max(0, 3 - u_data["daily_count"])
    bonus_left = u_data["bonus_videos"]
    ref_count = len(u_data["referrals"])
    
    admin_note = " (👑 Админ)" if user_id == ADMIN_ID else ""
    
    profile_text = TEXTS[lang]["profile"].format(
        name=message.from_user.first_name,
        admin_note=admin_note,
        user_id=user_id,
        daily=daily_left,
        bonus=bonus_left,
        refs=ref_count
    )
    await message.answer(profile_text, parse_mode="Markdown")

# ─── 6. ТУГМАИ ҚОИДАҲО ВА РЕФЕРАЛ ───
@dp.message(F.text.in_({"📜 Қоидаҳо ва Линки рефералӣ", "📜 Правила и Рефералка", "📜 Rules & Referral"}))
async def info_cmd(message: types.Message):
    user_id = str(message.from_user.id)
    lang = get_lang(user_id)
    ref_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
    
    rules_text = TEXTS[lang]["rules_ref"].format(ref_link=ref_link)
    await message.answer(rules_text, parse_mode="Markdown")

# ─── 7. КОРКАРДИ ВИДЕОҲО ───
@dp.message(F.video | F.video_note)
async def handle_video(message: types.Message):
    user_id = str(message.from_user.id)
    lang = get_lang(user_id)
    
    if not await check_sub(message.from_user.id):
        await start_cmd(message, CommandObject(command="start"))
        return

    video_obj = message.video or message.video_note
    if video_obj.file_size > 19 * 1024 * 1024:
        try: await message.delete()
        except: pass
        await message.answer(TEXTS[lang]["video_big"])
        return

    # Тафтиши лимит барои корбарони оддӣ
    if user_id != ADMIN_ID:
        all_data = get_user_data(user_id)
        u_data = all_data[user_id]
        
        daily_left = 3 - u_data["daily_count"]
        bonus_left = u_data["bonus_videos"]

        if daily_left <= 0 and bonus_left <= 0:
            ref_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
            await message.answer(
                TEXTS[lang]["limit_end"].format(ref_link=ref_link),
                parse_mode="Markdown"
            )
            return

        if daily_left > 0:
            u_data["daily_count"] += 1
        else:
            u_data["bonus_videos"] -= 1
        save_data(all_data)

    status_msg = await message.answer(TEXTS[lang]["processing"])
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
        await status_msg.edit_text(TEXTS[lang]["movie_title"].format(title=movie_name), reply_markup=keyboard)
    except Exception as e:
        await status_msg.edit_text(f"❌ Хатогӣ / Ошибка: {e}")
    finally:
        if os.path.exists(video_path): os.remove(video_path)

# ─── 8. CATCH-ALL БАРОИ ПАЁМҲОИ ДИГАР ───
@dp.message()
async def unhandled_messages(message: types.Message):
    lang = get_lang(str(message.from_user.id))
    await message.answer(TEXTS[lang]["send_only_video"])

# ─── ИҶРОҲОИ АВВАЛИН ВА СТАРТ ───
async def main():
    dp.startup.register(notify_users_on_restart)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
