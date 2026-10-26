require('dotenv').config();
const { Telegraf, Markup } = require('telegraf');
const http = require('http');
const db = require('./database');

const BOT_TOKEN = process.env.BOT_TOKEN || '';
if (!BOT_TOKEN) {
  console.error('XATOLIK: BOT_TOKEN topilmadi! .env faylini tekshiring.');
  process.exit(1);
}

const ADMIN_IDS = (process.env.ADMIN_IDS || '')
  .split(',')
  .map((id) => Number(id.trim()))
  .filter(Boolean);

const isAdmin = (userId) => ADMIN_IDS.includes(Number(userId));

const bot = new Telegraf(BOT_TOKEN);

// ================= Veb-server (Render / UptimeRobot uchun) ================= //
const PORT = process.env.PORT || 3000;
http.createServer((req, res) => {
  res.writeHead(200, { 'Content-Type': 'text/plain; charset=utf-8' });
  res.end('🎬 Kino Bot faol ishlamoqda (24/7)! 🚀');
}).listen(PORT, () => {
  console.log(`🌐 Web server ${PORT}-portda ishga tushdi.`);
});

// Admin holatlarini saqlash (In-Memory State)
const adminState = new Map();

// ================= Klaviaturashar ================= //
function getMainKeyboard() {
  return Markup.keyboard([
    ['🔍 Kod orqali kinoni topish'],
    ['🎲 Tasodifiy kino', '🆕 So\'nggi kinolar'],
    ['🔥 TOP kinolar', 'ℹ️ Bot haqida']
  ]).resize();
}

function getAdminKeyboard() {
  return Markup.keyboard([
    ['🎬 Kino qo\'shish', '🗑 Kino o\'chirish'],
    ['📢 Kanallar sozlamasi', '📊 Statistika'],
    ['✉️ Xabar yuborish (Reklama)', '🔙 Asosiy menyu']
  ]).resize();
}

function getCancelKeyboard() {
  return Markup.keyboard([['❌ Bekor qilish']]).resize();
}

function getSkipCancelKeyboard() {
  return Markup.keyboard([['⏩ O\'tkazib yuborish', '❌ Bekor qilish']]).resize();
}

function getSubChannelsKeyboard(unsubscribed, movieCode = null) {
  const buttons = unsubscribed.map((ch, idx) => [
    Markup.button.url(`📢 ${idx + 1}. ${ch.name}`, ch.invite_link)
  ]);
  const cbData = movieCode ? `check_sub:${movieCode}` : 'check_sub:none';
  buttons.push([Markup.button.callback('✅ Obuna bo\'ldim (Tekshirish)', cbData)]);
  return Markup.inlineKeyboard(buttons);
}

function getMovieShareKeyboard(code, botUsername) {
  const url = `https://t.me/share/url?url=https://t.me/${botUsername}?start=${code}&text=Kino%20kodi:%20${code}`;
  return Markup.inlineKeyboard([[Markup.button.url('↗️ Do\'stlarga ulashish', url)]]);
}

function getSearchResultsKeyboard(movies) {
  const buttons = movies.map((m) => [
    Markup.button.callback(`🎬 ${m.title} (Kod: ${m.code})`, `get_movie:${m.code}`)
  ]);
  return Markup.inlineKeyboard(buttons);
}

function getChannelsManageKeyboard(channels) {
  const buttons = channels.map((ch) => [
    Markup.button.callback(`🗑 ${ch.name}`, `del_chan:${ch.channel_id}`)
  ]);
  buttons.push([Markup.button.callback('➕ Yangi kanal qo\'shish', 'add_new_channel')]);
  buttons.push([Markup.button.callback('🔙 Orqaga', 'admin_close_channels')]);
  return Markup.inlineKeyboard(buttons);
}

// ================= Obunani tekshirish ================= //
async function checkUserSubscriptions(telegram, userId) {
  const channels = db.getAllChannels();
  if (!channels.length) return { isSubscribed: true, unsubscribed: [] };

  const unsubscribed = [];
  for (const ch of channels) {
    try {
      const member = await telegram.getChatMember(ch.channel_id, userId);
      if (!['creator', 'administrator', 'member', 'restricted'].includes(member.status)) {
        unsubscribed.push(ch);
      }
    } catch (err) {
      console.warn(`Kanalni tekshirishda ogohlantirish (${ch.channel_id}):`, err.message);
    }
  }
  return { isSubscribed: unsubscribed.length === 0, unsubscribed };
}

// Kinoni yuborish
async function sendMovieToUser(ctx, movie) {
  const botUsername = ctx.botInfo.username;
  let caption = `🎬 <b>${movie.title}</b>\n\n` +
    `🔢 <b>Kodi:</b> <code>${movie.code}</code>\n` +
    `👁 <b>Ko'rishlar soni:</b> ${movie.views}\n`;
  if (movie.description) {
    caption += `📝 <b>Tavsif:</b> ${movie.description}\n`;
  }
  caption += `\n🤖 Bizning bot: @${botUsername}`;

  await ctx.replyWithVideo(movie.file_id, {
    caption: caption,
    parse_mode: 'HTML',
    ...getMovieShareKeyboard(movie.code, botUsername)
  });
}

// ================= /start komandasi ================= //
bot.start(async (ctx) => {
  const user = ctx.from;
  db.addUser(user.id, user.username, user.first_name);

  // Deep linking (masalan /start 101)
  const payload = ctx.startPayload ? ctx.startPayload.trim() : null;
  const targetCode = payload && /^\d+$/.test(payload) ? Number(payload) : null;

  const { isSubscribed, unsubscribed } = await checkUserSubscriptions(ctx.telegram, user.id);
  if (!isSubscribed) {
    return ctx.reply(
      `👋 Assalomu alaykum, <b>${user.first_name || ''}</b>!\n\n` +
      `Botdan to'liq foydalanish va kinoni yuklab olish uchun quyidagi kanallarga a'zo bo'ling:`,
      {
        parse_mode: 'HTML',
        ...getSubChannelsKeyboard(unsubscribed, targetCode)
      }
    );
  }

  if (targetCode) {
    const movie = db.getMovie(targetCode);
    if (movie) return sendMovieToUser(ctx, movie);
  }

  return ctx.reply(
    `👋 Assalomu alaykum, <b>${user.first_name || ''}</b>!\n\n` +
    `🎬 <b>Kino Botiga xush kelibsiz!</b>\n\n` +
    `Kerakli kinoni olish uchun uning <b>kodini</b> yuboring (masalan: <code>1</code>) yoki kino <b>nomini</b> yozib qidiring.`,
    {
      parse_mode: 'HTML',
      ...getMainKeyboard()
    }
  );
});

// ================= Obunani tekshirish Callbacki ================= //
bot.action(/^check_sub:(.+)$/, async (ctx) => {
  const codeStr = ctx.match[1];
  const userId = ctx.from.id;

  const { isSubscribed, unsubscribed } = await checkUserSubscriptions(ctx.telegram, userId);
  if (!isSubscribed) {
    return ctx.answerCbQuery('❌ Hali barcha kanallarga a\'zo bo\'lmadingiz! Iltimos, a\'zo bo\'lib qayta tekshiring.', { show_alert: true });
  }

  try {
    await ctx.deleteMessage();
  } catch {}

  await ctx.reply('✅ <b>Obuna tasdiqlandi! Xush kelibsiz!</b>', {
    parse_mode: 'HTML',
    ...getMainKeyboard()
  });

  if (codeStr && codeStr !== 'none' && /^\d+$/.test(codeStr)) {
    const movie = db.getMovie(Number(codeStr));
    if (movie) await sendMovieToUser(ctx, movie);
  }
  return ctx.answerCbQuery();
});

// Inline orqali kino tanlanganda
bot.action(/^get_movie:(\d+)$/, async (ctx) => {
  const code = Number(ctx.match[1]);
  const userId = ctx.from.id;

  const { isSubscribed, unsubscribed } = await checkUserSubscriptions(ctx.telegram, userId);
  if (!isSubscribed) {
    await ctx.answerCbQuery('Kanalga a\'zo bo\'lishingiz kerak!', { show_alert: true });
    return ctx.reply('⚠️ Botdan foydalanish uchun quyidagi kanallarga a\'zo bo\'ling:', getSubChannelsKeyboard(unsubscribed, code));
  }

  const movie = db.getMovie(code);
  if (movie) {
    await sendMovieToUser(ctx, movie);
    return ctx.answerCbQuery();
  }
  return ctx.answerCbQuery('Kino topilmadi!', { show_alert: true });
});

// ================= Admin Boshqaruvi ================= //
bot.command('admin', async (ctx) => {
  if (!isAdmin(ctx.from.id)) return;
  adminState.delete(ctx.from.id);
  return ctx.reply(
    `🛠 <b>Admin Boshqaruv Paneliga xush kelibsiz!</b>\n\nKerakli bo'limni tanlang:`,
    { parse_mode: 'HTML', ...getAdminKeyboard() }
  );
});

bot.hears('🔙 Asosiy menyu', async (ctx) => {
  if (!isAdmin(ctx.from.id)) return;
  adminState.delete(ctx.from.id);
  return ctx.reply('🏠 Asosiy foydalanuvchi menyusiga qaytdingiz.', getMainKeyboard());
});

bot.hears('❌ Bekor qilish', async (ctx) => {
  if (!isAdmin(ctx.from.id)) return;
  adminState.delete(ctx.from.id);
  return ctx.reply('❌ Jarayon bekor qilindi.', getAdminKeyboard());
});

// 🎬 Kino qo'shish
bot.hears('🎬 Kino qo\'shish', async (ctx) => {
  if (!isAdmin(ctx.from.id)) return;
  adminState.set(ctx.from.id, { step: 'ADD_CODE' });
  return ctx.reply(
    '🔢 Yangi kino uchun <b>raqamli kod</b> kiriting (masalan: <code>101</code>):',
    { parse_mode: 'HTML', ...getCancelKeyboard() }
  );
});

// 🗑 Kino o'chirish
bot.hears('🗑 Kino o\'chirish', async (ctx) => {
  if (!isAdmin(ctx.from.id)) return;
  adminState.set(ctx.from.id, { step: 'DEL_CODE' });
  return ctx.reply(
    '🗑 O\'chirmoqchi bo\'lgan kinoning <b>kodini</b> kiriting:',
    { parse_mode: 'HTML', ...getCancelKeyboard() }
  );
});

// 📊 Statistika
bot.hears('📊 Statistika', async (ctx) => {
  if (!isAdmin(ctx.from.id)) return;

  const usersCount = db.getTotalUsersCount();
  const moviesCount = db.getTotalMoviesCount();
  const channels = db.getAllChannels();
  const topMovies = db.getTopMovies(5);

  let topText = '';
  if (topMovies.length) {
    topMovies.forEach((m, idx) => {
      topText += `${idx + 1}. 🎬 <b>${m.title}</b> (Kod: <code>${m.code}</code>) — 👁 ${m.views} marta\n`;
    });
  } else {
    topText = 'Hozircha kinolar ko\'rilmagan.\n';
  }

  const text = `📊 <b>Bot Statistikasi:</b>\n\n` +
    `👥 <b>Foydalanuvchilar:</b> ${usersCount} ta\n` +
    `🎬 <b>Bazada kinolar:</b> ${moviesCount} ta\n` +
    `📢 <b>Majburiy obuna kanallari:</b> ${channels.length} ta\n\n` +
    `🔥 <b>TOP 5 Ko'rilgan kinolar:</b>\n${topText}`;

  return ctx.reply(text, { parse_mode: 'HTML' });
});

// 📢 Kanallar sozlamasi
bot.hears('📢 Kanallar sozlamasi', async (ctx) => {
  if (!isAdmin(ctx.from.id)) return;
  const channels = db.getAllChannels();
  const text = channels.length
    ? '📢 <b>Majburiy obuna kanallari:</b>\nO\'chirmoqchi bo\'lgan kanal ustiga bosing:'
    : '📢 Hozirda majburiy obuna uchun kanallar qo\'shilmagan.';
  return ctx.reply(text, { parse_mode: 'HTML', ...getChannelsManageKeyboard(channels) });
});

bot.action(/^del_chan:(.+)$/, async (ctx) => {
  if (!isAdmin(ctx.from.id)) return ctx.answerCbQuery('Ruxsat yo\'q!', { show_alert: true });
  const chanId = ctx.match[1];
  db.deleteChannel(chanId);
  await ctx.answerCbQuery('✅ Kanal o\'chirildi!', { show_alert: true });

  const channels = db.getAllChannels();
  const text = channels.length
    ? '📢 <b>Majburiy obuna kanallari:</b>\nO\'chirmoqchi bo\'lgan kanal ustiga bosing:'
    : '📢 Hozirda majburiy obuna uchun kanallar qo\'shilmagan.';
  return ctx.editMessageText(text, { parse_mode: 'HTML', ...getChannelsManageKeyboard(channels) });
});

bot.action('admin_close_channels', async (ctx) => {
  try {
    await ctx.deleteMessage();
  } catch {}
});

bot.action('add_new_channel', async (ctx) => {
  if (!isAdmin(ctx.from.id)) return ctx.answerCbQuery('Ruxsat yo\'q!', { show_alert: true });
  try {
    await ctx.deleteMessage();
  } catch {}
  adminState.set(ctx.from.id, { step: 'CHAN_ID' });
  return ctx.reply(
    '📢 Kanal ID yoki Username\'ini kiriting (masalan: <code>@mening_kanalim</code> yoki <code>-1001234567890</code>):\n\n' +
    '<i>Eslatma: Bot ushbu kanalda <b>Admin</b> bo\'lishi shart!</i>',
    { parse_mode: 'HTML', ...getCancelKeyboard() }
  );
});

// ✉️ Xabar yuborish (Reklama)
bot.hears('✉️ Xabar yuborish (Reklama)', async (ctx) => {
  if (!isAdmin(ctx.from.id)) return;
  adminState.set(ctx.from.id, { step: 'BROADCAST_MSG' });
  return ctx.reply(
    '📢 Barcha foydalanuvchilarga yubormoqchi bo\'lgan xabaringizni yuboring.\n(Bu rasm, video, matn yoki formatlangan post bo\'lishi mumkin):',
    getCancelKeyboard()
  );
});

bot.action('confirm_broadcast', async (ctx) => {
  if (!isAdmin(ctx.from.id)) return;
  const state = adminState.get(ctx.from.id);
  if (!state || !state.broadcastMsgId) return ctx.answerCbQuery('Xabar topilmadi!');

  adminState.delete(ctx.from.id);
  await ctx.editMessageText('⏳ Xabar tarqatish boshlandi... Iltimos kuting.');

  const userIds = db.getAllUserIds();
  let sent = 0;
  let blocked = 0;

  for (const uid of userIds) {
    try {
      await ctx.telegram.copyMessage(uid, state.fromChatId, state.broadcastMsgId);
      sent++;
      await new Promise((r) => setTimeout(r, 40));
    } catch {
      blocked++;
    }
  }

  return ctx.reply(
    `✅ <b>Xabar tarqatish yakunlandi!</b>\n\n` +
    `📨 Yetib bordi: <b>${sent} ta</b>\n` +
    `🚫 Bloklagan/Xatolik: <b>${blocked} ta</b>`,
    { parse_mode: 'HTML', ...getAdminKeyboard() }
  );
});

bot.action('cancel_broadcast', async (ctx) => {
  adminState.delete(ctx.from.id);
  try {
    await ctx.editMessageText('❌ Reklama yuborish bekor qilindi.');
  } catch {}
  return ctx.reply('Asosiy panel:', getAdminKeyboard());
});

// ================= Foydalanuvchi Menyusi ================= //
bot.hears(['🔍 Kod orqali kinoni topish', 'Kod orqali kinoni topish', '🔍 Kod orqali topish'], async (ctx) => {
  const { isSubscribed, unsubscribed } = await checkUserSubscriptions(ctx.telegram, ctx.from.id);
  if (!isSubscribed) {
    return ctx.reply('⚠️ Botdan foydalanish uchun quyidagi kanallarga a\'zo bo\'ling:', getSubChannelsKeyboard(unsubscribed));
  }
  return ctx.reply(
    '🔢 <b>Kino kodini kiriting:</b>\n\nMarhamat, ko\'rmoqchi bo\'lgan kino kodini yuboring (masalan: <code>1</code> yoki <code>101</code>):',
    { parse_mode: 'HTML' }
  );
});

bot.hears('🎲 Tasodifiy kino', async (ctx) => {
  const { isSubscribed, unsubscribed } = await checkUserSubscriptions(ctx.telegram, ctx.from.id);
  if (!isSubscribed) {
    return ctx.reply('⚠️ Botdan foydalanish uchun quyidagi kanallarga a\'zo bo\'ling:', getSubChannelsKeyboard(unsubscribed));
  }

  const movie = db.getRandomMovie();
  if (movie) {
    let text = `🎲 <b>Tasodifiy kino:</b>\n\n` +
      `🎬 <b>Nomi:</b> ${movie.title}\n` +
      `🔢 <b>Kodi:</b> <code>${movie.code}</code>\n`;
    if (movie.description) {
      text += `📝 <b>Tavsif:</b> ${movie.description}\n`;
    }
    text += `\n<i>Kinoni tomosha qilish uchun uning kodini (<code>${movie.code}</code>) botga yuboring.</i>`;
    return ctx.reply(text, { parse_mode: 'HTML' });
  }
  return ctx.reply('😔 Hozircha bazada birorta ham kino mavjud emas.');
});

bot.hears('🆕 So\'nggi kinolar', async (ctx) => {
  const { isSubscribed, unsubscribed } = await checkUserSubscriptions(ctx.telegram, ctx.from.id);
  if (!isSubscribed) {
    return ctx.reply('⚠️ Botdan foydalanish uchun quyidagi kanallarga a\'zo bo\'ling:', getSubChannelsKeyboard(unsubscribed));
  }

  const movies = db.getLatestMovies(10);
  if (!movies.length) return ctx.reply('😔 Hozircha bazada kinolar mavjud emas.');

  let text = '🆕 <b>Eng so\'nggi yuklangan kinolar:</b>\n\n';
  movies.forEach((m) => {
    text += `🎬 <b>${m.title}</b> — Kodi: <code>${m.code}</code>\n`;
  });
  text += '\n<i>Kinoni tomosha qilish uchun uning kodini botga yuboring.</i>';
  return ctx.reply(text, { parse_mode: 'HTML' });
});

bot.hears('🔥 TOP kinolar', async (ctx) => {
  const { isSubscribed, unsubscribed } = await checkUserSubscriptions(ctx.telegram, ctx.from.id);
  if (!isSubscribed) {
    return ctx.reply('⚠️ Botdan foydalanish uchun quyidagi kanallarga a\'zo bo\'ling:', getSubChannelsKeyboard(unsubscribed));
  }

  const movies = db.getTopMovies(8);
  if (!movies.length) return ctx.reply('😔 Hozircha kinolar ro\'yxati bo\'sh.');

  let text = '🔥 <b>Eng ko\'p ko\'rilgan TOP kinolar:</b>\n\n';
  movies.forEach((m, idx) => {
    text += `${idx + 1}. 🎬 <b>${m.title}</b> (Kod: <code>${m.code}</code>) — 👁 ${m.views}\n`;
  });
  text += '\n<i>Kinoni tomosha qilish uchun uning kodini botga yuboring.</i>';
  return ctx.reply(text, { parse_mode: 'HTML' });
});

bot.hears('ℹ️ Bot haqida', async (ctx) => {
  const text = '🎬 <b>Kino Bot haqida ma\'lumot:</b>\n\n' +
    'Bu bot orqali siz xohlagan kinongizni tez va qulay yuklab olishingiz mumkin.\n\n' +
    '🔍 <b>Kino qidirish usullari:</b>\n' +
    '1. Kino <b>kodini</b> yuboring (masalan: <code>1</code> yoki <code>101</code>).\n' +
    '2. Kino <b>nomini</b> yozing (masalan: <i>Forsaj</i> yoki <i>Titanik</i>).\n\n' +
    'Maroqli tomosha tilaymiz! 🍿';
  return ctx.reply(text, { parse_mode: 'HTML' });
});

// ================= Umumiy Xabarlar (Admin FSM va Qidiruv) ================= //
bot.on('message', async (ctx) => {
  const userId = ctx.from.id;
  const state = adminState.get(userId);

  // 1. Admin FSM jarayoni
  if (state && isAdmin(userId)) {
    // Kino kodi bosqichi
    if (state.step === 'ADD_CODE') {
      const text = ctx.message.text ? ctx.message.text.trim() : '';
      if (!/^\d+$/.test(text)) {
        return ctx.reply('⚠️ Iltimos, faqat butun sonli kod kiriting (masalan: <code>105</code>):', { parse_mode: 'HTML' });
      }
      const code = Number(text);
      if (db.movieExists(code)) {
        return ctx.reply(`⚠️ <b>${code}</b> kodli kino allaqachon mavjud! Boshqa kod kiriting:`, { parse_mode: 'HTML' });
      }
      state.code = code;
      state.step = 'ADD_TITLE';
      return ctx.reply('📝 Endi <b>kino nomini</b> kiriting (masalan: <i>Qasoskorlar: Intiho</i>):', { parse_mode: 'HTML' });
    }

    // Kino nomi bosqichi
    if (state.step === 'ADD_TITLE') {
      const text = ctx.message.text ? ctx.message.text.trim() : '';
      if (!text) return ctx.reply('⚠️ Iltimos, kino nomini matn shaklida yozing:');
      state.title = text;
      state.step = 'ADD_DESC';
      return ctx.reply(
        'ℹ️ Kino haqida qisqacha tavsif/janr yozing (yoki <b>⏩ O\'tkazib yuborish</b> tugmasini bosing):',
        { parse_mode: 'HTML', ...getSkipCancelKeyboard() }
      );
    }

    // Kino tavsifi bosqichi
    if (state.step === 'ADD_DESC') {
      const text = ctx.message.text ? ctx.message.text.trim() : '';
      if (['⏩ O\'tkazib yuborish', 'O\'tkazib yuborish', '-', '/skip'].includes(text)) {
        state.description = '';
      } else {
        state.description = text;
      }
      state.step = 'ADD_VIDEO';
      return ctx.reply(
        '📹 Endi <b>kinoning videosini</b> yuboring (yoki kanaldan forward qiling):',
        { parse_mode: 'HTML', ...getCancelKeyboard() }
      );
    }

    // Kino videosi bosqichi
    if (state.step === 'ADD_VIDEO') {
      const video = ctx.message.video;
      if (!video) {
        return ctx.reply('⚠️ Iltimos, video fayl yuboring:');
      }
      const fileId = video.file_id;
      db.addMovie(state.code, state.title, fileId, state.description);
      adminState.delete(userId);

      return ctx.reply(
        `✅ <b>Kino muvaffaqiyatli saqlandi!</b>\n\n` +
        `🎬 <b>Nomi:</b> ${state.title}\n` +
        `🔢 <b>Kodi:</b> <code>${state.code}</code>\n\n` +
        `Foydalanuvchilar endi <code>${state.code}</code> kodini yozib ushbu kinoni yuklab olishlari mumkin.`,
        { parse_mode: 'HTML', ...getAdminKeyboard() }
      );
    }

    // Kino o'chirish bosqichi
    if (state.step === 'DEL_CODE') {
      const text = ctx.message.text ? ctx.message.text.trim() : '';
      if (!/^\d+$/.test(text)) {
        return ctx.reply('⚠️ Iltimos, faqat butun sonli kod kiriting:');
      }
      const code = Number(text);
      const success = db.deleteMovie(code);
      adminState.delete(userId);
      if (success) {
        return ctx.reply(`✅ <code>${code}</code> kodli kino bazadan o'chirildi.`, { parse_mode: 'HTML', ...getAdminKeyboard() });
      }
      return ctx.reply(`❌ <code>${code}</code> kodli kino bazadan topilmadi.`, { parse_mode: 'HTML', ...getAdminKeyboard() });
    }

    // Kanal ID bosqichi
    if (state.step === 'CHAN_ID') {
      const text = ctx.message.text ? ctx.message.text.trim() : '';
      state.channelId = text;
      state.step = 'CHAN_NAME';
      return ctx.reply('📝 Kanal nomini kiriting (tugmada ko\'rinadigan nom, masalan: <i>Kino Olami</i>):', { parse_mode: 'HTML' });
    }

    // Kanal nomi bosqichi
    if (state.step === 'CHAN_NAME') {
      const text = ctx.message.text ? ctx.message.text.trim() : '';
      state.channelName = text;
      state.step = 'CHAN_LINK';
      return ctx.reply('🔗 Kanalga taklif havolasini (link) kiriting (masalan: <code>https://t.me/mening_kanalim</code>):', { parse_mode: 'HTML' });
    }

    // Kanal linki bosqichi
    if (state.step === 'CHAN_LINK') {
      const text = ctx.message.text ? ctx.message.text.trim() : '';
      db.addChannel(state.channelId, state.channelName, text);
      adminState.delete(userId);
      return ctx.reply(
        `✅ <b>Kanal muvaffaqiyatli qo'shildi!</b>\n\n` +
        `📢 Nomi: ${state.channelName}\n` +
        `🆔 ID: <code>${state.channelId}</code>\n` +
        `🔗 Link: ${text}`,
        { parse_mode: 'HTML', ...getAdminKeyboard() }
      );
    }

    // Reklama xabari bosqichi
    if (state.step === 'BROADCAST_MSG') {
      state.broadcastMsgId = ctx.message.message_id;
      state.fromChatId = ctx.chat.id;
      state.step = 'BROADCAST_CONFIRM';
      const totalUsers = db.getTotalUsersCount();
      return ctx.reply(
        `Ushbu xabar <b>${totalUsers} ta</b> foydalanuvchiga yuboriladi.\n\nXabarni tasdiqlaysizmi?`,
        {
          parse_mode: 'HTML',
          ...Markup.inlineKeyboard([
            [
              Markup.button.callback('✅ Ha, yuborilsin', 'confirm_broadcast'),
              Markup.button.callback('❌ Bekor qilish', 'cancel_broadcast')
            ]
          ])
        }
      );
    }
  }

  // 2. Foydalanuvchi xabarlari (Kod yoki Nom orqali qidiruv)
  const text = ctx.message.text ? ctx.message.text.trim() : '';
  if (!text) return;

  const { isSubscribed, unsubscribed } = await checkUserSubscriptions(ctx.telegram, userId);

  // Faqat raqam (kod) yozilgan bo'lsa
  if (/^\d+$/.test(text)) {
    const code = Number(text);
    if (!isSubscribed) {
      return ctx.reply('⚠️ Kinoni olish uchun quyidagi kanallarga a\'zo bo\'ling:', getSubChannelsKeyboard(unsubscribed, code));
    }

    const movie = db.getMovie(code);
    if (movie) {
      return sendMovieToUser(ctx, movie);
    }
    return ctx.reply(
      `❌ <b>${code}</b> kodli kino topilmadi.\n\nIltimos, kodni to'g'ri yozganingizga ishonch hosil qiling yoki kino nomini yozib qidiring.`,
      { parse_mode: 'HTML' }
    );
  }

  // Nom orqali qidiruv
  if (!isSubscribed) {
    return ctx.reply('⚠️ Botdan foydalanish uchun quyidagi kanallarga a\'zo bo\'ling:', getSubChannelsKeyboard(unsubscribed));
  }

  const results = db.searchMovies(text, 8);
  if (results.length) {
    return ctx.reply(
      `🔍 <b>"${text}"</b> bo'yicha topilgan kinolar:`,
      { parse_mode: 'HTML', ...getSearchResultsKeyboard(results) }
    );
  }

  return ctx.reply(
    `❌ <b>"${text}"</b> bo'yicha hech narsa topilmadi.\nKino kodini kiritib ko'ring yoki boshqacha nom bilan qidiring.`,
    { parse_mode: 'HTML' }
  );
});

// Xatoliklarni ushlash (Bot qulab tushmasligi uchun)
bot.catch((err, ctx) => {
  console.error(`Xatolik yuz berdi (${ctx.updateType}):`, err.message);
});

// ================= Ishga tushirish ================= //
bot.telegram.getMe().then((botInfo) => {
  console.log('==================================================');
  console.log('[+] KINO BOT ISHGA TUSHDI! (Node.js Telegraf)');
  console.log(`[*] Bot Username: @${botInfo.username}`);
  console.log(`[*] Admin ID lar: [${ADMIN_IDS.join(', ')}]`);
  console.log('==================================================');
}).catch((err) => {
  console.error('❌ Bot tokenini tekshirishda xatolik:', err.message);
});

bot.launch({ dropPendingUpdates: true }).catch((err) => {
  if (err.message && err.message.includes('409')) {
    console.error('❌ XATOLIK: 409 Conflict. Ushbu bot boshqa joyda allaqachon ishlayapti!');
  } else {
    console.error('❌ Bot launch xatoligi:', err.message);
  }
});

// To'xtatish signallari
process.once('SIGINT', () => bot.stop('SIGINT'));
process.once('SIGTERM', () => bot.stop('SIGTERM'));
