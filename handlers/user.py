import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, CommandObject

from database import db
from middlewares.sub_checker import check_user_subscriptions
from keyboards.user_kb import (
    get_main_keyboard,
    get_sub_channels_kb,
    get_search_results_kb,
    get_movie_share_kb
)

router = Router()
logger = logging.getLogger(__name__)

async def send_movie_to_user(bot: Bot, chat_id: int, movie: dict):
    """Foydalanuvchiga kinoni yuborish uchun yordamchi funksiya"""
    bot_info = await bot.get_me()
    caption = (
        f"🎬 <b>{movie['title']}</b>\n\n"
        f"🔢 <b>Kodi:</b> <code>{movie['code']}</code>\n"
        f"👁 <b>Ko'rishlar soni:</b> {movie['views']}\n"
    )
    if movie.get("description"):
        caption += f"📝 <b>Tavsif:</b> {movie['description']}\n"
    caption += f"\n🤖 Bizning bot: @{bot_info.username}"

    share_kb = get_movie_share_kb(movie["code"], bot_info.username)
    await bot.send_video(
        chat_id=chat_id,
        video=movie["file_id"],
        caption=caption,
        parse_mode="HTML",
        reply_markup=share_kb
    )

# /start komandasi
@router.message(CommandStart())
async def start_handler(message: Message, command: CommandObject, bot: Bot):
    user = message.from_user
    await db.add_user(user.id, user.username, user.first_name)

    # Deep linking (masalan t.me/bot?start=101)
    target_code = None
    if command.args and command.args.isdigit():
        target_code = int(command.args)

    # Majburiy obunani tekshirish
    is_sub, unsubscribed = await check_user_subscriptions(bot, user.id)
    if not is_sub:
        await message.answer(
            f"👋 Assalomu alaykum, <b>{user.first_name}</b>!\n\n"
            "Botdan to'liq foydalanish va kinoni yuklab olish uchun quyidagi kanallarga a'zo bo'ling:",
            parse_mode="HTML",
            reply_markup=get_sub_channels_kb(unsubscribed, movie_code=target_code)
        )
        return

    # Agar start orqali kino kodi berilgan bo'lsa
    if target_code:
        movie = await db.get_movie(target_code)
        if movie:
            await send_movie_to_user(bot, message.chat.id, movie)
            return

    await message.answer(
        f"👋 Assalomu alaykum, <b>{user.first_name}</b>!\n\n"
        "🎬 <b>Kino Botiga xush kelibsiz!</b>\n\n"
        "Kerakli kinoni olish uchun uning <b>kodini</b> yuboring (masalan: <code>101</code>) "
        "yoki kino <b>nomini</b> yozib qidiring.",
        parse_mode="HTML",
        reply_markup=get_main_keyboard()
    )

# Obunani tekshirish callbacki
@router.callback_query(F.data.startswith("check_sub:"))
async def check_sub_callback(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    data_parts = callback.data.split("check_sub:")
    code_str = data_parts[1] if len(data_parts) > 1 else "none"

    is_sub, unsubscribed = await check_user_subscriptions(bot, user_id)
    if not is_sub:
        await callback.answer("❌ Hali barcha kanallarga a'zo bo'lmadingiz! Iltimos, a'zo bo'lib qayta tekshiring.", show_alert=True)
        return

    await callback.message.delete()
    await callback.message.answer(
        "✅ <b>Obuna tasdiqlandi! Xush kelibsiz!</b>",
        parse_mode="HTML",
        reply_markup=get_main_keyboard()
    )

    # Agar avval so'ralgan kino kodi bo'lsa, o'shani darhol yuboramiz
    if code_str != "none" and code_str.isdigit():
        code = int(code_str)
        movie = await db.get_movie(code)
        if movie:
            await send_movie_to_user(bot, callback.message.chat.id, movie)

# Inline orqali kino tanlanganda
@router.callback_query(F.data.startswith("get_movie:"))
async def get_movie_callback(callback: CallbackQuery, bot: Bot):
    code = int(callback.data.split("get_movie:")[1])
    is_sub, unsubscribed = await check_user_subscriptions(bot, callback.from_user.id)
    if not is_sub:
        await callback.answer("Kanalga a'zo bo'lishingiz kerak!", show_alert=True)
        await callback.message.answer(
            "⚠️ Botdan foydalanish uchun quyidagi kanallarga a'zo bo'ling:",
            reply_markup=get_sub_channels_kb(unsubscribed, movie_code=code)
        )
        return

    movie = await db.get_movie(code)
    if movie:
        await send_movie_to_user(bot, callback.message.chat.id, movie)
        await callback.answer()
    else:
        await callback.answer("Kino topilmadi!", show_alert=True)

# 🔍 Kod orqali kinoni topish
@router.message(F.text.in_(["🔍 Kod orqali kinoni topish", "Kod orqali kinoni topish", "🔍 Kod orqali topish"]))
async def ask_movie_code_handler(message: Message, bot: Bot):
    is_sub, unsubscribed = await check_user_subscriptions(bot, message.from_user.id)
    if not is_sub:
        await message.answer(
            "⚠️ Botdan foydalanish uchun quyidagi kanallarga a'zo bo'ling:",
            reply_markup=get_sub_channels_kb(unsubscribed)
        )
        return

    await message.answer(
        "🔢 <b>Kino kodini kiriting:</b>\n\n"
        "Marhamat, ko'rmoqchi bo'lgan kino kodini yuboring (masalan: <code>1</code> yoki <code>101</code>):",
        parse_mode="HTML"
    )

# 🎲 Tasodifiy kino (Faqat nomi va kodi chiqadi, video tashlanmaydi)
@router.message(F.text == "🎲 Tasodifiy kino")
async def random_movie_handler(message: Message, bot: Bot):
    is_sub, unsubscribed = await check_user_subscriptions(bot, message.from_user.id)
    if not is_sub:
        await message.answer(
            "⚠️ Botdan foydalanish uchun quyidagi kanallarga a'zo bo'ling:",
            reply_markup=get_sub_channels_kb(unsubscribed)
        )
        return

    movie = await db.get_random_movie()
    if movie:
        text = (
            f"🎲 <b>Tasodifiy kino:</b>\n\n"
            f"🎬 <b>Nomi:</b> {movie['title']}\n"
            f"🔢 <b>Kodi:</b> <code>{movie['code']}</code>\n"
        )
        if movie.get("description"):
            text += f"📝 <b>Tavsif:</b> {movie['description']}\n"
        text += f"\n<i>Kinoni tomosha qilish uchun uning kodini (<code>{movie['code']}</code>) botga yuboring.</i>"
        await message.answer(text, parse_mode="HTML")
    else:
        await message.answer("😔 Hozircha bazada birorta ham kino mavjud emas.")

# 🆕 So'nggi kinolar (Faqat nomi va kodi chiqadi)
@router.message(F.text == "🆕 So'nggi kinolar")
async def latest_movies_handler(message: Message, bot: Bot):
    is_sub, unsubscribed = await check_user_subscriptions(bot, message.from_user.id)
    if not is_sub:
        await message.answer(
            "⚠️ Botdan foydalanish uchun quyidagi kanallarga a'zo bo'ling:",
            reply_markup=get_sub_channels_kb(unsubscribed)
        )
        return

    movies = await db.get_latest_movies(limit=10)
    if not movies:
        await message.answer("😔 Hozircha bazada kinolar mavjud emas.")
        return

    text = "🆕 <b>Eng so'nggi yuklangan kinolar:</b>\n\n"
    for m in movies:
        text += f"🎬 <b>{m['title']}</b> — Kodi: <code>{m['code']}</code>\n"
    text += "\n<i>Kinoni tomosha qilish uchun uning kodini botga yuboring.</i>"

    await message.answer(text, parse_mode="HTML")

# 🔥 TOP kinolar
@router.message(F.text == "🔥 TOP kinolar")
async def top_movies_handler(message: Message, bot: Bot):
    is_sub, unsubscribed = await check_user_subscriptions(bot, message.from_user.id)
    if not is_sub:
        await message.answer(
            "⚠️ Botdan foydalanish uchun quyidagi kanallarga a'zo bo'ling:",
            reply_markup=get_sub_channels_kb(unsubscribed)
        )
        return

    movies = await db.get_top_movies(limit=8)
    if not movies:
        await message.answer("😔 Hozircha kinolar ro'yxati bo'sh.")
        return

    text = "🔥 <b>Eng ko'p ko'rilgan TOP kinolar:</b>\n\n"
    for idx, m in enumerate(movies, 1):
        text += f"{idx}. 🎬 <b>{m['title']}</b> (Kod: <code>{m['code']}</code>) — 👁 {m['views']}\n"
    text += "\n<i>Kinoni ko'rish uchun uning kodini yuboring.</i>"

    await message.answer(text, parse_mode="HTML")

# ℹ️ Bot haqida
@router.message(F.text == "ℹ️ Bot haqida")
async def about_handler(message: Message):
    text = (
        "🎬 <b>Kino Bot haqida ma'lumot:</b>\n\n"
        "Bu bot orqali siz xohlagan kinongizni tez va qulay yuklab olishingiz mumkin.\n\n"
        "🔍 <b>Kino qidirish usullari:</b>\n"
        "1. Kino <b>kodini</b> yuboring (masalan: <code>101</code>).\n"
        "2. Kino <b>nomini</b> yozing (masalan: <i>Titanik</i> yoki <i>Marvel</i>).\n\n"
        "Maroqli tomosha tilaymiz! 🍿"
    )
    await message.answer(text, parse_mode="HTML")

# Matnli xabarlar (Kino kodi yoki nomi)
@router.message(F.text)
async def handle_search_or_code(message: Message, bot: Bot):
    text = message.text.strip()
    user_id = message.from_user.id

    # Obunani tekshirish
    is_sub, unsubscribed = await check_user_subscriptions(bot, user_id)

    # 1. Agar foydalanuvchi faqat raqam (kod) yuborgan bo'lsa
    if text.isdigit():
        code = int(text)
        if not is_sub:
            await message.answer(
                "⚠️ Kinoni olish uchun quyidagi kanallarga a'zo bo'ling:",
                reply_markup=get_sub_channels_kb(unsubscribed, movie_code=code)
            )
            return

        movie = await db.get_movie(code)
        if movie:
            await send_movie_to_user(bot, message.chat.id, movie)
        else:
            await message.answer(
                f"❌ <b>{code}</b> kodli kino topilmadi.\n\n"
                "Iltimos, kodni to'g'ri yozganingizga ishonch hosil qiling yoki kino nomini yozib qidiring.",
                parse_mode="HTML"
            )
        return

    # 2. Agar foydalanuvchi kino nomini yozgan bo'lsa (Qidiruv)
    if not is_sub:
        await message.answer(
            "⚠️ Botdan foydalanish uchun quyidagi kanallarga a'zo bo'ling:",
            reply_markup=get_sub_channels_kb(unsubscribed)
        )
        return

    results = await db.search_movies(text, limit=8)
    if results:
        await message.answer(
            f"🔍 <b>\"{text}\"</b> bo'yicha topilgan kinolar:",
            parse_mode="HTML",
            reply_markup=get_search_results_kb(results)
        )
    else:
        await message.answer(
            f"❌ <b>\"{text}\"</b> bo'yicha hech narsa topilmadi.\n"
            "Kino kodini kiritib ko'ring yoki boshqacha nom bilan qidiring.",
            parse_mode="HTML"
        )
