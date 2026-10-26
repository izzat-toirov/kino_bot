@echo off
title Kino Bot - Ishga tushirish
chcp 65001 > nul
echo ===================================================
echo             KINO BOT ISHGA TUSHMOQDA...
echo ===================================================

echo Kerakli kutubxonalar tekshirilmoqda...
python -m pip install -r requirements.txt

echo.
echo Bot ishga tushirilmoqda...
python bot.py

echo.
echo Bot to'xtadi.
pause
