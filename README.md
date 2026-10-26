# 🎬 Telegram Kino Boti (aiogram 3.x)

Telegram uchun eng zamonaviy, to‘liq asinxron (`aiosqlite` + `aiogram 3`), tezkor va qotishlarsiz ishlaydigan professional Kino Bot loyihasi.

---

## 🚀 Asosiy Imkoniyatlari

* ⚡ **Tezkor va Qotishlarsiz (Asinxron):** `aiosqlite` orqali ma'lumotlar bazasi bilan uzluksiz, parallel ishlaydi. Ko'p foydalanuvchi bir vaqtda kirsa ham aslo qotmaydi.
* 🆓 **100% Tekin Video Saqlash:** Kinolarni serverga yuklash shart emas. Telegramning o‘z `file_id` mexanizmidan foydalanadi. Serveringizda xotira (disk) to'lmaydi.
* 🔢 **Kod orqali kino olish:** Masalan, `101`, `102` deb yozsa, bir zumda video yuboriladi.
* 🔗 **Deep-linking:** Kanalingizga `https://t.me/bot_username?start=101` havolasini qo'ysangiz, odamlar bitta bosishda kinoni botdan oladi.
* 🔍 **Nom orqali aqlli qidiruv:** Foydalanuvchi kino kodini bilmasa, uning nomini (masalan: *Titanik*, *Avatar*) yozsa, mos kinolar ro'yxatini chiqarib beradi.
* 📢 **Majburiy Obuna (Avtomatik tekshiruv):** Botga xohlagancha kanal qo'shish mumkin. Odamlar kanallaringizga a'zo bo'lmaguncha botdan kino ololmaydi.
* 🛠 **Qulay Admin Panel (`/admin`):**
  - 🎬 **Kino qo'shish:** Kod, nom, tavsif va videoni yuborish orqali.
  - 🗑 **Kino o'chirish:** Kodini kiritish orqali bazadan o'chirish.
  - 📢 **Kanallar sozlamasi:** Kanallarni qo'shish va o'chirish.
  - 📊 **To'liq Statistika:** Jami foydalanuvchilar, kinolar, TOP ko'rilgan filmlar.
  - ✉️ **Reklama tarqatish (Broadcast):** Barcha a'zolarga rasm, video, matnli xabarlarni xavfsiz (Telegram limitlariga moslab) yuborish.
* 🎲 **Tasodifiy kino va TOP kinolar:** Foydalanuvchilar zerikmasligi uchun yangi filmlarni kashf qilish tugmalari.

---

## 📁 Loyiha Tuzilishi

```text
kino_bot/
├── .env                <-- Bot Token va Admin ID yoziladi
├── .env.example        <-- Namuna
├── bot.py              <-- Asosiy ishga tushiruvchi fayl
├── config.py           <-- Sozlamalarni o'quvchi modul
├── database.py         <-- Asinxron SQLite ma'lumotlar bazasi
├── requirements.txt    <-- Kerakli Python kutubxonalari
├── run.bat             <-- Windowsda bitta bosishda ishga tushirish
├── handlers/
│   ├── admin.py        <-- Admin paneli va buyruqlari
│   └── user.py         <-- Foydalanuvchi buyruqlari va qidiruv
├── keyboards/
│   ├── admin_kb.py     <-- Admin tugmalari
│   └── user_kb.py      <-- Foydalanuvchi va majburiy obuna tugmalari
└── middlewares/
    └── sub_checker.py  <-- Majburiy obunani tekshirish mexanizmi
```

---

## ⚙️ O'rnatish va Ishga Tushirish

### 1-qadam: Token va Admin ID kiritish
`kino_bot` papkasidagi `.env` faylini oching:
```env
BOT_TOKEN=7123456789:AAExampleTokenHere
ADMIN_IDS=123456789
DATABASE_PATH=kino_bot.db
```
* **BOT_TOKEN** — [@BotFather](https://t.me/BotFather) dan olingan token.
* **ADMIN_IDS** — O'zingizning Telegram ID raqamingiz ([@userinfobot](https://t.me/userinfobot) orqali bilib olishingiz mumkin).

### 2-qadam: Ishga tushirish
Windows kompyuterda:
* Shunchaki **`run.bat`** fayli ustiga 2 marta bosing!
* Yoki terminalda:
  ```bash
  python bot.py
  ```

---

## 💡 Botdan Foydalanish Bo'yicha Maslahatlar

1. **Kino qo'shish:**
   - Botga kiring va `/admin` buyrug'ini bering.
   - **🎬 Kino qo'shish** tugmasini bosing.
   - Kino kodi, nomi va videosini ketma-ket yuboring.
2. **Majburiy obuna qo'shish:**
   - O'zingizning kanalingizga botingizni **Admin** qilib qo'shing.
   - `/admin` menyusida **📢 Kanallar sozlamasi** -> **➕ Yangi kanal qo'shish** ni bosing.
   - Kanal username yoki ID'sini, nomini va linkini yozing.
3. **Kinolarni saqlash:**
   - Bitta shaxsiy yopiq kanal ochib qo'ying ("Kino Ombor"). Kinolarni o'sha yerga tashlab, bot orqali forward qilib qo'shsangiz, kinolar hech qachon o'chib ketmaydi.

---

## 🌐 24/7 Bepul Serverga Qo'yish (Hosting)

Bot kompyuteringiz o'chganda ham to'xtamasligi uchun:
1. **[Render.com](https://render.com):**
   - Bepul hisob ochasiz.
   - Ushbu papkani GitHub-ga yuklab, Render'da **Background Worker** sifatida ulab qo'yasiz.
2. **[Koyeb.com](https://koyeb.com):**
   - GitHub-dan to'g'ridan-to'g'ri bepul ishga tushirish imkoni mavjud.
3. **Android Termux:**
   - Agar qo'lingizda eskiroq Android telefon bo'lsa, Termux ilovasida Python o'rnatib, kodni Wi-Fi orqali tunu-kun ishlatib qo'yishingiz mumkin.
