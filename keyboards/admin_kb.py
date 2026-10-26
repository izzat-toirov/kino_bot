from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from typing import List, Dict, Any

def get_admin_main_kb() -> ReplyKeyboardMarkup:
    """Admin boshqaruv paneli menyusi"""
    kb = [
        [KeyboardButton(text="🎬 Kino qo'shish"), KeyboardButton(text="🗑 Kino o'chirish")],
        [KeyboardButton(text="📢 Kanallar sozlamasi"), KeyboardButton(text="📊 Statistika")],
        [KeyboardButton(text="✉️ Xabar yuborish (Reklama)"), KeyboardButton(text="🔙 Asosiy menyu")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_cancel_kb() -> ReplyKeyboardMarkup:
    """Jarayonni bekor qilish tugmasi"""
    kb = [[KeyboardButton(text="❌ Bekor qilish")]]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_skip_cancel_kb() -> ReplyKeyboardMarkup:
    """O'tkazib yuborish va bekor qilish tugmalari"""
    kb = [
        [KeyboardButton(text="⏩ O'tkazib yuborish"), KeyboardButton(text="❌ Bekor qilish")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_channels_manage_kb(channels: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Kanallarni ko'rish va o'chirish klaviaturasi"""
    inline_kb = []
    for ch in channels:
        inline_kb.append([
            InlineKeyboardButton(
                text=f"🗑 {ch['name']}",
                callback_data=f"del_chan:{ch['channel_id']}"
            )
        ])
    inline_kb.append([
        InlineKeyboardButton(text="➕ Yangi kanal qo'shish", callback_data="add_new_channel")
    ])
    inline_kb.append([
        InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_close_channels")
    ])
    return InlineKeyboardMarkup(inline_keyboard=inline_kb)

def get_broadcast_confirm_kb() -> InlineKeyboardMarkup:
    """Xabar tarqatishni tasdiqlash klaviaturasi"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Ha, yuborilsin", callback_data="confirm_broadcast"),
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_broadcast")
            ]
        ]
    )
