import asyncio
import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import is_admin
from database import db
from keyboards.admin_kb import (
    get_admin_main_kb,
    get_cancel_kb,
    get_skip_cancel_kb,
    get_channels_manage_kb,
    get_broadcast_confirm_kb
)
from keyboards.user_kb import get_main_keyboard

router = Router()
logger = logging.getLogger(__name__)

# FSM Holatlari
class AddMovieState(StatesGroup):
    code = State()
    title = State()
    description = State()
    video = State()

class DeleteMovieState(StatesGroup):
    code = State()

class AddChannelState(StatesGroup):
    channel_id = State()
    name = State()
    invite_link = State()

class BroadcastState(StatesGroup):
    message = State()
    confirmation = State()

# Bekor qilish tugmasi uchun umumiy handler
@router.message(F.text == "❌ Bekor qilish")
async def cancel_handler(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    await message.answer("❌ Jarayon bekor qilindi.", reply_markup=get_admin_main_kb())

# Admin panelga kirish
@router.message(Command("admin"))
async def admin_panel(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    await message.answer(
        "🛠 <b>Admin Boshqaruv Paneliga xush kelibsiz!</b>\n\n"
        "Kerakli bo'limni tanlang:",
        parse_mode="HTML",
        reply_markup=get_admin_main_kb()
    )

# Asosiy menyuga qaytish
@router.message(F.text == "🔙 Asosiy menyu")
async def back_to_user_menu(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    await message.answer("🏠 Asosiy foydalanuvchi menyusiga qaytdingiz.", reply_markup=get_main_keyboard())

# ==================== KINO QO'SHISH ====================
@router.message(F.text == "🎬 Kino qo'shish")
async def start_add_movie(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    await message.answer(
        "🔢 Yangi kino uchun <b>raqamli kod</b> kiriting (masalan: <code>101</code>):",
        parse_mode="HTML",
        reply_markup=get_cancel_kb()
    )
    await state.set_state(AddMovieState.code)

@router.message(AddMovieState.code)
async def process_movie_code(message: Message, state: FSMContext):
    if not message.text or not message.text.isdigit():
        await message.answer("⚠️ Iltimos, faqat butun sonli kod kiriting (masalan: <code>105</code>):", parse_mode="HTML")
        return
    
    code = int(message.text.strip())
    if await db.movie_exists(code):
        await message.answer(f"⚠️ <b>{code}</b> kodli kino allaqachon mavjud! Boshqa kod kiriting:")
        return
    
    await state.update_data(code=code)
    await message.answer("📝 Endi <b>kino nomini</b> kiriting (masalan: <i>Qasoskorlar: Intiho</i>):", parse_mode="HTML")
    await state.set_state(AddMovieState.title)

@router.message(AddMovieState.title)
async def process_movie_title(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("⚠️ Iltimos, kino nomini matn shaklida yozing:")
        return
    
    title = message.text.strip()
    await state.update_data(title=title)
    await message.answer(
        "ℹ️ Kino haqida qisqacha tavsif/janr yozing (yoki <b>⏩ O'tkazib yuborish</b> tugmasini bosing):",
        parse_mode="HTML",
        reply_markup=get_skip_cancel_kb()
    )
    await state.set_state(AddMovieState.description)

@router.message(AddMovieState.description)
async def process_movie_description(message: Message, state: FSMContext):
    raw_text = message.text.strip() if message.text else ""
    if raw_text in ["⏩ O'tkazib yuborish", "O'tkazib yuborish", "-", "/skip"]:
        desc = ""
    else:
        desc = raw_text

    await state.update_data(description=desc)
    await message.answer(
        "📹 Endi <b>kinoning videosini</b> yuboring (yoki kanaldan forward qiling):",
        parse_mode="HTML",
        reply_markup=get_cancel_kb()
    )
    await state.set_state(AddMovieState.video)

@router.message(AddMovieState.video, F.video)
async def process_movie_video(message: Message, state: FSMContext):
    data = await state.get_data()
    code = data["code"]
    title = data["title"]
    description = data.get("description", "")
    file_id = message.video.file_id

    success = await db.add_movie(code=code, title=title, file_id=file_id, description=description)
    await state.clear()

    if success:
        await message.answer(
            f"✅ <b>Kino muvaffaqiyatli saqlandi!</b>\n\n"
            f"🎬 <b>Nomi:</b> {title}\n"
            f"🔢 <b>Kodi:</b> <code>{code}</code>\n\n"
            f"Foydalanuvchilar endi <code>{code}</code> kodini yozib ushbu kinoni yuklab olishlari mumkin.",
            parse_mode="HTML",
            reply_markup=get_admin_main_kb()
        )
    else:
        await message.answer("❌ Kinoni saqlashda xatolik yuz berdi.", reply_markup=get_admin_main_kb())

# ==================== KINO O'CHIRISH ====================
@router.message(F.text == "🗑 Kino o'chirish")
async def start_delete_movie(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    await message.answer(
        "🗑 O'chirmoqchi bo'lgan kinoning <b>kodini</b> kiriting:",
        parse_mode="HTML",
        reply_markup=get_cancel_kb()
    )
    await state.set_state(DeleteMovieState.code)

@router.message(DeleteMovieState.code)
async def process_delete_movie(message: Message, state: FSMContext):
    if not message.text or not message.text.isdigit():
        await message.answer("⚠️ Iltimos, faqat butun sonli kod kiriting:")
        return

    code = int(message.text.strip())
    success = await db.delete_movie(code)
    await state.clear()

    if success:
        await message.answer(f"✅ <code>{code}</code> kodli kino bazadan o'chirildi.", parse_mode="HTML", reply_markup=get_admin_main_kb())
    else:
        await message.answer(f"❌ <code>{code}</code> kodli kino bazadan topilmadi.", parse_mode="HTML", reply_markup=get_admin_main_kb())

# ==================== STATISTIKA ====================
@router.message(F.text == "📊 Statistika")
async def show_statistics(message: Message):
    if not is_admin(message.from_user.id):
        return

    users_count = await db.get_total_users_count()
    movies_count = await db.get_total_movies_count()
    channels = await db.get_all_channels()
    top_movies = await db.get_top_movies(limit=5)

    top_text = ""
    if top_movies:
        for idx, m in enumerate(top_movies, 1):
            top_text += f"{idx}. 🎬 <b>{m['title']}</b> (Kod: <code>{m['code']}</code>) — 👁 {m['views']} marta\n"
    else:
        top_text = "Hozircha kinolar ko'rilmagan.\n"

    text = (
        "📊 <b>Bot Statistikasi:</b>\n\n"
        f"👥 <b>Foydalanuvchilar:</b> {users_count} ta\n"
        f"🎬 <b>Bazada kinolar:</b> {movies_count} ta\n"
        f"📢 <b>Majburiy obuna kanallari:</b> {len(channels)} ta\n\n"
        f"🔥 <b>TOP 5 Ko'rilgan kinolar:</b>\n{top_text}"
    )
    await message.answer(text, parse_mode="HTML")

# ==================== KANALLAR SOZLAMASI ====================
@router.message(F.text == "📢 Kanallar sozlamasi")
async def manage_channels(message: Message):
    if not is_admin(message.from_user.id):
        return

    channels = await db.get_all_channels()
    if not channels:
        text = "📢 Hozirda majburiy obuna uchun kanallar qo'shilmagan."
    else:
        text = "📢 <b>Majburiy obuna kanallari:</b>\nO'chirmoqchi bo'lgan kanal ustiga bosing:"
    
    await message.answer(text, reply_markup=get_channels_manage_kb(channels), parse_mode="HTML")

@router.callback_query(F.data.startswith("del_chan:"))
async def delete_channel_cb(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q!", show_alert=True)
        return

    channel_id = callback.data.split("del_chan:")[1]
    await db.delete_channel(channel_id)
    await callback.answer("✅ Kanal o'chirildi!", show_alert=True)

    channels = await db.get_all_channels()
    if not channels:
        text = "📢 Hozirda majburiy obuna uchun kanallar qo'shilmagan."
    else:
        text = "📢 <b>Majburiy obuna kanallari:</b>\nO'chirmoqchi bo'lgan kanal ustiga bosing:"

    await callback.message.edit_text(text, reply_markup=get_channels_manage_kb(channels), parse_mode="HTML")

@router.callback_query(F.data == "admin_close_channels")
async def close_channels_cb(callback: CallbackQuery):
    await callback.message.delete()

@router.callback_query(F.data == "add_new_channel")
async def start_add_channel(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q!", show_alert=True)
        return

    await callback.message.delete()
    await callback.message.answer(
        "📢 Kanal ID yoki Username'ini kiriting (masalan: <code>@mening_kanalim</code> yoki <code>-1001234567890</code>):\n\n"
        "<i>Eslatma: Bot ushbu kanalda <b>Admin</b> bo'lishi shart!</i>",
        parse_mode="HTML",
        reply_markup=get_cancel_kb()
    )
    await state.set_state(AddChannelState.channel_id)

@router.message(AddChannelState.channel_id)
async def process_channel_id(message: Message, state: FSMContext):
    channel_id = message.text.strip()
    await state.update_data(channel_id=channel_id)
    await message.answer("📝 Kanal nomini kiriting (tugmada ko'rinadigan nom, masalan: <i>Kino Olami</i>):", parse_mode="HTML")
    await state.set_state(AddChannelState.name)

@router.message(AddChannelState.name)
async def process_channel_name(message: Message, state: FSMContext):
    name = message.text.strip()
    await state.update_data(name=name)
    await message.answer("🔗 Kanalga taklif havolasini (link) kiriting (masalan: <code>https://t.me/mening_kanalim</code>):", parse_mode="HTML")
    await state.set_state(AddChannelState.invite_link)

@router.message(AddChannelState.invite_link)
async def process_channel_link(message: Message, state: FSMContext):
    invite_link = message.text.strip()
    data = await state.get_data()
    channel_id = data["channel_id"]
    name = data["name"]

    success = await db.add_channel(channel_id=channel_id, name=name, invite_link=invite_link)
    await state.clear()

    if success:
        await message.answer(
            f"✅ <b>Kanal muvaffaqiyatli qo'shildi!</b>\n\n"
            f"📢 Nomi: {name}\n"
            f"🆔 ID: <code>{channel_id}</code>\n"
            f"🔗 Link: {invite_link}",
            parse_mode="HTML",
            reply_markup=get_admin_main_kb()
        )
    else:
        await message.answer("❌ Kanalni saqlashda xatolik yuz berdi.", reply_markup=get_admin_main_kb())

# ==================== XABAR YUBORISH (REKLAMA) ====================
@router.message(F.text == "✉️ Xabar yuborish (Reklama)")
async def start_broadcast(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    await message.answer(
        "📢 Barcha foydalanuvchilarga yubormoqchi bo'lgan xabaringizni yuboring.\n"
        "(Bu rasm, video, matn yoki formatlangan post bo'lishi mumkin):",
        reply_markup=get_cancel_kb()
    )
    await state.set_state(BroadcastState.message)

@router.message(BroadcastState.message)
async def process_broadcast_message(message: Message, state: FSMContext):
    total_users = await db.get_total_users_count()
    await state.update_data(msg_id=message.message_id, from_chat_id=message.chat.id)

    await message.answer(
        f"Ushbu xabar <b>{total_users} ta</b> foydalanuvchiga yuboriladi.\n\n"
        "Xabarni tasdiqlaysizmi?",
        parse_mode="HTML",
        reply_markup=get_broadcast_confirm_kb()
    )
    await state.set_state(BroadcastState.confirmation)

@router.callback_query(BroadcastState.confirmation, F.data == "confirm_broadcast")
async def execute_broadcast(callback: CallbackQuery, state: FSMContext, bot: Bot):
    if not is_admin(callback.from_user.id):
        return

    data = await state.get_data()
    msg_id = data["msg_id"]
    from_chat_id = data["from_chat_id"]
    await state.clear()

    await callback.message.edit_text("⏳ Xabar tarqatish boshlandi... Iltimos kuting.")

    user_ids = await db.get_all_user_ids()
    sent_count = 0
    blocked_count = 0

    for uid in user_ids:
        try:
            await bot.copy_message(chat_id=uid, from_chat_id=from_chat_id, message_id=msg_id)
            sent_count += 1
            await asyncio.sleep(0.04)  # Rate-limit va qotishdan himoya
        except Exception:
            blocked_count += 1

    await callback.message.answer(
        f"✅ <b>Xabar tarqatish yakunlandi!</b>\n\n"
        f"📨 Yetib bordi: <b>{sent_count} ta</b>\n"
        f"🚫 Bloklagan/Xatolik: <b>{blocked_count} ta</b>",
        parse_mode="HTML",
        reply_markup=get_admin_main_kb()
    )

@router.callback_query(BroadcastState.confirmation, F.data == "cancel_broadcast")
async def cancel_broadcast_cb(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Reklama yuborish bekor qilindi.")
    await callback.message.answer("Asosiy panel:", reply_markup=get_admin_main_kb())
