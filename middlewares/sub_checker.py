import logging
from typing import Tuple, List, Dict, Any
from aiogram import Bot
from database import db

logger = logging.getLogger(__name__)

async def check_user_subscriptions(bot: Bot, user_id: int) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    Foydalanuvchi barcha majburiy obuna kanallariga a'zo bo'lganini tekshiradi.
    Qaytaradi: (barchasiga_azo_mi: bool, a'zo_bolinmagan_kanallar: list)
    """
    channels = await db.get_all_channels()
    if not channels:
        return True, []

    unsubscribed = []
    for ch in channels:
        channel_id = ch["channel_id"]
        try:
            member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
            # member statusi: creator, administrator, member, restricted (agar kanalni o'qiy olsa)
            if member.status not in ["creator", "administrator", "member", "restricted"]:
                unsubscribed.append(ch)
        except Exception as e:
            # Agar bot kanalda admin bo'lmasa yoki kanal topilmasa, xatolik berib qotib qolmasligi uchun
            logger.warning(f"Kanalni tekshirishda xatolik ({channel_id}): {e}")
            continue

    return len(unsubscribed) == 0, unsubscribed
