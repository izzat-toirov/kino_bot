@echo off
title Kino Bot (Node.js) - Ishga tushirish
chcp 65001 > nul
echo ===================================================
echo       KINO BOT (NODE.JS) ISHGA TUSHMOQDA...
echo ===================================================

echo Kerakli paketlar tekshirilmoqda...
call npm.cmd install

echo.
echo Bot ishga tushirilmoqda...
node bot.js

echo.
echo Bot to'xtadi.
pause
