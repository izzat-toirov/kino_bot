from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from typing import List, Dict, Any, Optional

def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Asosiy menyu klaviaturasi"""
    kb = [
        [KeyboardButton(text="🔍 Kod orqali kinoni topish")],
        [KeyboardButton(text="🎲 Tasodifiy kino"), KeyboardButton(text="🆕 So'nggi kinolar")],
        [KeyboardButton(text="🔥 TOP kinolar"), KeyboardButton(text="ℹ️ Bot haqida")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_sub_channels_kb(channels: List[Dict[str, Any]], movie_code: Optional[int] = None) -> InlineKeyboardMarkup:
    """Majburiy obuna kanallari klaviaturasi"""
    inline_kb = []
    for idx, ch in enumerate(channels, 1):
        inline_kb.append([
            InlineKeyboardButton(text=f"📢 {idx}. {ch['name']}", url=ch['invite_link'])
        ])
    
    cb_data = f"check_sub:{movie_code}" if movie_code is not None else "check_sub:none"
    inline_kb.append([
        InlineKeyboardButton(text="✅ Obuna bo'ldim (Tekshirish)", callback_data=cb_data)
    ])
    return InlineKeyboardMarkup(inline_keyboard=inline_kb)

def get_search_results_kb(movies: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Kino qidiruv natijalari klaviaturasi"""
    inline_kb = []
    for m in movies:
        inline_kb.append([
            InlineKeyboardButton(
                text=f"🎬 {m['title']} (Kod: {m['code']})",
                callback_data=f"get_movie:{m['code']}"
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=inline_kb)

def get_movie_share_kb(movie_code: int, bot_username: str) -> InlineKeyboardMarkup:
    """Kino tagidagi ulashish tugmasi"""
    share_url = f"https://t.me/share/url?url=https://t.me/{bot_username}?start={movie_code}&text=Kino%20kodi:%20{movie_code}"
    inline_kb = [
        [InlineKeyboardButton(text="↗️ Do'stlarga ulashish", url=share_url)]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_kb)
