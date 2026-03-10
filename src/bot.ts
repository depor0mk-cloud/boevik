import { Bot, Context, session, SessionFlavor } from 'grammy';
import dotenv from 'dotenv';
import { db, getSettings } from './firebase.js';

dotenv.config();

interface SessionData {
  step?: string;
  clanName?: string;
  clanTag?: string;
}

type MyContext = Context & SessionFlavor<SessionData>;

export const bot = new Bot<MyContext>(process.env.TELEGRAM_BOT_TOKEN!);

bot.use(session({ initial: (): SessionData => ({}) }));

const ADMIN_USERNAME = process.env.ADMIN_USERNAME || 'Trim_peek';

// Middleware to check bot status
bot.use(async (ctx, next) => {
  const username = ctx.from?.username;
  const settings = await getSettings();

  if (settings.bot_disabled && username !== ADMIN_USERNAME) {
    await ctx.reply('🛠 Бот на тех.перерыве');
    return;
  }

  if (settings.test_mode && username !== ADMIN_USERNAME) {
    await ctx.reply('🔧 Бот на тестовом осмотре');
    return;
  }

  return next();
});

bot.command('профиль', async (ctx) => {
  const uid = ctx.from?.id.toString();
  const userSnap = await db.ref(`users/${uid}`).once('value');
  const user = userSnap.val() || { gold: 0, exp: 0, level: 1 };

  const text = `👤 <b>Профиль: ${ctx.from?.first_name}</b>\n` +
    `📈 Уровень: ${user.level || 1}\n` +
    `✨ Опыт: ${user.exp || 0}\n` +
    `💰 Личный вклад: ${user.contribution || 0}\n` +
    `🏰 Клан: ${user.clan_id ? 'Состоит' : 'Нет'}`;

  await ctx.reply(text, { parse_mode: 'HTML' });
});

bot.command('топ', async (ctx) => {
  const clansSnap = await db.ref('clans').once('value');
  const clans = clansSnap.val() || {};
  
  const sortedClans = Object.values(clans).sort((a: any, b: any) => b.gold - a.gold).slice(0, 10);
  
  let text = '🏆 <b>Топ 10 кланов по золоту:</b>\n\n';
  sortedClans.forEach((clan: any, index: number) => {
    text += `${index + 1}. ${clan.name} [${clan.tag}] - ${clan.gold} 💰\n`;
  });

  await ctx.reply(text, { parse_mode: 'HTML' });
});
bot.command('start', async (ctx) => {
  await ctx.reply('👋 Добро пожаловать в Боевик Бот!\nИспользуйте /правило чтобы узнать как играть.');
});

bot.command('правило', async (ctx) => {
  await ctx.reply(
    '📜 <b>Правила игры:</b>\n' +
    '1. Создавайте кланы или вступайте в существующие.\n' +
    '2. Работайте (/работа), чтобы пополнять казну клана.\n' +
    '3. Стройте заводы для пассивного дохода.\n' +
    '4. Лидеры могут объявлять войны и проводить мобилизацию.\n' +
    '5. Разрабатывайте ракеты для сокрушительных ударов.\n' +
    '6. Уважайте других игроков.',
    { parse_mode: 'HTML' }
  );
});

// --- CLAN MANAGEMENT ---

bot.command('создать', async (ctx) => {
  const args = ctx.match.split(' ');
  if (args.length < 3 || args[0].toLowerCase() !== 'клан') {
    await ctx.reply('⚠️ Использование: <code>/создать клан [название] [тег]</code>', { parse_mode: 'HTML' });
    return;
  }

  const name = args[1];
  const tag = args[2].toUpperCase();

  // Check if user is already in a clan
  const userRef = db.ref(`users/${ctx.from?.id}`);
  const userSnap = await userRef.once('value');
  const user = userSnap.val();

  if (user?.clan_id) {
    await ctx.reply('Вы уже в клане. Покиньте его, чтобы создать новый.');
    return;
  }

  // Check uniqueness
  const clansSnap = await db.ref('clans').once('value');
  const clans = clansSnap.val() || {};
  for (const cid in clans) {
    if (clans[cid].name.toLowerCase() === name.toLowerCase() || clans[cid].tag === tag) {
      await ctx.reply('⚠️ Клан с таким названием или тегом уже существует.');
      return;
    }
  }

  ctx.session.clanName = name;
  ctx.session.clanTag = tag;

  await ctx.reply(`Будет создан клан ${name} [${tag}]. Вы уверены?`, {
    reply_markup: {
      inline_keyboard: [
        [
          { text: '✅ Да, создать', callback_data: 'confirm_create' },
          { text: '❌ Отмена', callback_data: 'cancel' }
        ]
      ]
    }
  });
});

bot.callbackQuery('confirm_create', async (ctx) => {
  const { clanName, clanTag } = ctx.session;
  if (!clanName || !clanTag) return;

  const clanRef = db.ref('clans').push();
  const clanId = clanRef.key;

  await clanRef.set({
    name: clanName,
    tag: clanTag,
    leader_id: ctx.from.id.toString(),
    members: [ctx.from.id.toString()],
    level: 1,
    exp: 0,
    hp: 1000,
    gold: 500,
    weapons: 0,
    army: { count: 0, strength: 0, experience: 0 },
    rockets: { ballistics: 0, nuclear: 0 },
    factories: {},
    productions: {},
    alliances: []
  });

  await db.ref(`users/${ctx.from.id}`).update({
    clan_id: clanId,
    role: 'leader',
    username: ctx.from.username || ctx.from.first_name
  });

  await ctx.editMessageText(`✅ Клан ${clanName} создан! Ты лидер.`);
  ctx.session = {};
});

bot.callbackQuery('cancel', async (ctx) => {
  await ctx.editMessageText('❌ Действие отменено.');
  ctx.session = {};
});

// --- ECONOMY ---

bot.command('работа', async (ctx) => {
  const uid = ctx.from?.id.toString();
  const userSnap = await db.ref(`users/${uid}`).once('value');
  const user = userSnap.val();

  if (!user?.clan_id) {
    await ctx.reply('⚠️ Вы не состояте в клане. Найдите или создайте клан, чтобы работать.');
    return;
  }

  const now = Date.now();
  const lastWork = user.last_work_1 || 0;
  if (now - lastWork < 6 * 3600 * 1000) {
    const remaining = Math.ceil((6 * 3600 * 1000 - (now - lastWork)) / 60000);
    await ctx.reply(`⏳ Вы устали. Отдохните еще ${Math.floor(remaining / 60)}ч ${remaining % 60}м.`);
    return;
  }

  const reward = Math.floor(Math.random() * 401) + 100;
  const clanRef = db.ref(`clans/${user.clan_id}`);
  const clanSnap = await clanRef.once('value');
  const clan = clanSnap.val();

  const newGold = (clan.gold || 0) + reward;
  await clanRef.update({ gold: newGold });

  await db.ref(`users/${uid}`).update({
    last_work_1: now,
    contribution: (user.contribution || 0) + reward,
    exp: (user.exp || 0) + 10
  });

  await ctx.reply(`➕ Клан получил ${reward} монет. Теперь в казне: ${newGold}. Ваш личный вклад: ${(user.contribution || 0) + reward} монет.`);
});

// --- ADMIN ---

bot.command('omg2105', async (ctx) => {
  if (ctx.from?.username !== ADMIN_USERNAME) return;
  
  await ctx.reply('🛠 <b>Админ-панель:</b>', {
    parse_mode: 'HTML',
    reply_markup: {
      inline_keyboard: [
        [
          { text: 'ВКЛ/ОТКЛ БОТА', callback_data: 'admin_toggle_bot' },
          { text: 'РЕЖИМ СНА', callback_data: 'admin_sleep' }
        ],
        [
          { text: 'РАССЫЛКА', callback_data: 'admin_broadcast' },
          { text: 'БЭКАП', callback_data: 'admin_backup' }
        ],
        [
          { text: '➡️ Далее', callback_data: 'admin_next' }
        ]
      ]
    }
  });
});

// --- CLAN MANAGEMENT ---

bot.command('мой_клан', async (ctx) => {
  const uid = ctx.from?.id.toString();
  const userSnap = await db.ref(`users/${uid}`).once('value');
  const user = userSnap.val();

  if (!user?.clan_id) {
    await ctx.reply('⚠️ Вы не состоите в клане.');
    return;
  }

  const clanSnap = await db.ref(`clans/${user.clan_id}`).once('value');
  const clan = clanSnap.val();

  if (!clan) {
    await ctx.reply('⚠️ Клан не найден.');
    return;
  }

  const text = `🏰 <b>Клан: ${clan.name} [${clan.tag}]</b>\n` +
    `👤 Лидер: ${clan.leader_id}\n` +
    `📈 Уровень: ${clan.level}\n` +
    `💰 Казна: ${clan.gold} золота\n` +
    `⚔️ Оружие: ${clan.weapons}\n` +
    `🛡 Здоровье: ${clan.hp}\n` +
    `👥 Участников: ${clan.members.length}`;

  await ctx.reply(text, { parse_mode: 'HTML' });
});

bot.command('список_кланов', async (ctx) => {
  const clansSnap = await db.ref('clans').once('value');
  const clans = clansSnap.val() || {};
  
  let text = '📋 <b>Список кланов:</b>\n\n';
  for (const cid in clans) {
    text += `• ${clans[cid].name} [${clans[cid].tag}] - Ур. ${clans[cid].level}\n`;
  }

  await ctx.reply(text, { parse_mode: 'HTML' });
});

bot.command('вступить', async (ctx) => {
  const args = ctx.match.split(' ');
  if (args.length < 1 || !args[0]) {
    await ctx.reply('⚠️ Использование: <code>/вступить [тег_клана]</code>', { parse_mode: 'HTML' });
    return;
  }

  const tag = args[0].toUpperCase();
  const clansSnap = await db.ref('clans').once('value');
  const clans = clansSnap.val() || {};
  
  let targetClanId = null;
  for (const cid in clans) {
    if (clans[cid].tag === tag) {
      targetClanId = cid;
      break;
    }
  }

  if (!targetClanId) {
    await ctx.reply('⚠️ Клан с таким тегом не найден.');
    return;
  }

  const userRef = db.ref(`users/${ctx.from?.id}`);
  const userSnap = await userRef.once('value');
  const user = userSnap.val();

  if (user?.clan_id) {
    await ctx.reply('⚠️ Вы уже в клане.');
    return;
  }

  // Add to clan
  const clan = clans[targetClanId];
  const members = clan.members || [];
  members.push(ctx.from?.id.toString());

  await db.ref(`clans/${targetClanId}`).update({ members });
  await userRef.update({
    clan_id: targetClanId,
    role: 'member',
    username: ctx.from?.username || ctx.from?.first_name
  });

  await ctx.reply(`✅ Вы вступили в клан ${clan.name}!`);
});

bot.command('выйти', async (ctx) => {
  const uid = ctx.from?.id.toString();
  const userRef = db.ref(`users/${uid}`);
  const userSnap = await userRef.once('value');
  const user = userSnap.val();

  if (!user?.clan_id) {
    await ctx.reply('⚠️ Вы не в клане.');
    return;
  }

  const clanRef = db.ref(`clans/${user.clan_id}`);
  const clanSnap = await clanRef.once('value');
  const clan = clanSnap.val();

  if (clan.leader_id === uid) {
    await ctx.reply('⚠️ Лидер не может выйти из клана. Передайте лидерство или удалите клан.');
    return;
  }

  const members = clan.members.filter((m: string) => m !== uid);
  await clanRef.update({ members });
  await userRef.update({ clan_id: null, role: null });

  await ctx.reply(`✅ Вы вышли из клана ${clan.name}.`);
});

// --- FACTORIES ---

bot.command('завод', async (ctx) => {
  await ctx.reply('🏭 <b>Меню заводов:</b>\nВыберите действие:', {
    parse_mode: 'HTML',
    reply_markup: {
      inline_keyboard: [
        [
          { text: '🏗 Построить завод', callback_data: 'factory_build' },
          { text: '🏭 Мои заводы', callback_data: 'factory_list' }
        ],
        [
          { text: '⬆️ Апгрейд', callback_data: 'factory_upgrade' }
        ]
      ]
    }
  });
});

bot.callbackQuery('factory_build', async (ctx) => {
  await ctx.editMessageText('🏗 <b>Выберите тип завода:</b>', {
    parse_mode: 'HTML',
    reply_markup: {
      inline_keyboard: [
        [
          { text: '💰 Финансовый (1000 золота)', callback_data: 'build_finance' },
          { text: '⚔️ Оружейный (1250 золота)', callback_data: 'build_weapon' }
        ],
        [
          { text: '🔙 Назад', callback_data: 'factory_back' }
        ]
      ]
    }
  });
});

bot.callbackQuery(/^build_(finance|weapon)$/, async (ctx) => {
  const type = ctx.match[1] as 'finance' | 'weapon';
  const uid = ctx.from.id.toString();
  const userSnap = await db.ref(`users/${uid}`).once('value');
  const user = userSnap.val();

  if (!user?.clan_id || user.role !== 'leader') {
    await ctx.answerCallbackQuery({ text: '⚠️ Только лидер может строить заводы.', show_alert: true });
    return;
  }

  const clanRef = db.ref(`clans/${user.clan_id}`);
  const clanSnap = await clanRef.once('value');
  const clan = clanSnap.val();

  const settings = await getSettings();
  const price = type === 'finance' ? settings.prices.factory_finance : settings.prices.factory_weapon;

  if (clan.gold < price) {
    await ctx.answerCallbackQuery({ text: '❌ Недостаточно золота в казне.', show_alert: true });
    return;
  }

  const factoryRef = clanRef.child('factories').push();
  await factoryRef.set({
    type,
    level: 1,
    last_production: Date.now()
  });

  await clanRef.update({ gold: clan.gold - price });
  await ctx.editMessageText(`✅ Завод (${type === 'finance' ? 'Финансовый' : 'Оружейный'}) построен! Списано ${price} золота.`);
});

bot.callbackQuery('factory_list', async (ctx) => {
  const uid = ctx.from.id.toString();
  const userSnap = await db.ref(`users/${uid}`).once('value');
  const user = userSnap.val();

  if (!user?.clan_id) return;

  const clanSnap = await db.ref(`clans/${user.clan_id}`).once('value');
  const clan = clanSnap.val();

  if (!clan.factories || Object.keys(clan.factories).length === 0) {
    await ctx.editMessageText('⚠️ У вашего клана пока нет заводов.', {
      reply_markup: {
        inline_keyboard: [[{ text: '🔙 Назад', callback_data: 'factory_back' }]]
      }
    });
    return;
  }

  let text = '🏭 <b>Ваши заводы:</b>\n\n';
  for (const fid in clan.factories) {
    const f = clan.factories[fid];
    text += `• ${f.type === 'finance' ? '💰 Финансовый' : '⚔️ Оружейный'} - Ур. ${f.level}\n`;
  }

  await ctx.editMessageText(text, {
    parse_mode: 'HTML',
    reply_markup: {
      inline_keyboard: [[{ text: '🔙 Назад', callback_data: 'factory_back' }]]
    }
  });
});

bot.callbackQuery('factory_upgrade', async (ctx) => {
  const uid = ctx.from.id.toString();
  const userSnap = await db.ref(`users/${uid}`).once('value');
  const user = userSnap.val();

  if (!user?.clan_id || user.role !== 'leader') {
    await ctx.answerCallbackQuery({ text: '⚠️ Только лидер может улучшать заводы.', show_alert: true });
    return;
  }

  const clanSnap = await db.ref(`clans/${user.clan_id}`).once('value');
  const clan = clanSnap.val();

  if (!clan.factories || Object.keys(clan.factories).length === 0) {
    await ctx.answerCallbackQuery({ text: '⚠️ У вас нет заводов для улучшения.', show_alert: true });
    return;
  }

  const buttons = Object.keys(clan.factories).map(fid => {
    const f = clan.factories[fid];
    return [{ 
      text: `Улучшить ${f.type === 'finance' ? '💰' : '⚔️'} (Ур. ${f.level} -> ${f.level + 1})`, 
      callback_data: `up_f_${fid}` 
    }];
  });

  buttons.push([{ text: '🔙 Назад', callback_data: 'factory_back' }]);

  await ctx.editMessageText('⬆️ <b>Выберите завод для улучшения:</b>\nСтоимость: 1000 золота', {
    parse_mode: 'HTML',
    reply_markup: { inline_keyboard: buttons }
  });
});

bot.callbackQuery(/^up_f_(.+)$/, async (ctx) => {
  const fid = ctx.match[1];
  const uid = ctx.from.id.toString();
  const userSnap = await db.ref(`users/${uid}`).once('value');
  const user = userSnap.val();

  if (!user?.clan_id || user.role !== 'leader') return;

  const clanRef = db.ref(`clans/${user.clan_id}`);
  const clanSnap = await clanRef.once('value');
  const clan = clanSnap.val();

  const settings = await getSettings();
  const price = settings.prices.production_upgrade || 1000;

  if (clan.gold < price) {
    await ctx.answerCallbackQuery({ text: '❌ Недостаточно золота.', show_alert: true });
    return;
  }

  const factory = clan.factories[fid];
  if (!factory) return;

  await clanRef.child(`factories/${fid}`).update({ level: factory.level + 1 });
  await clanRef.update({ gold: clan.gold - price });

  await ctx.editMessageText(`✅ Завод улучшен до уровня ${factory.level + 1}!`);
});

bot.callbackQuery('factory_back', async (ctx) => {
  await ctx.editMessageText('🏭 <b>Меню заводов:</b>\nВыберите действие:', {
    parse_mode: 'HTML',
    reply_markup: {
      inline_keyboard: [
        [
          { text: '🏗 Построить завод', callback_data: 'factory_build' },
          { text: '🏭 Мои заводы', callback_data: 'factory_list' }
        ],
        [
          { text: '⬆️ Апгрейд', callback_data: 'factory_upgrade' }
        ]
      ]
    }
  });
});

bot.callbackQuery('admin_sleep', async (ctx) => {
  if (ctx.from.username !== ADMIN_USERNAME) return;
  const settings = await getSettings();
  const newState = !settings.sleep_mode;
  await db.ref('settings').update({ sleep_mode: newState });
  await ctx.answerCallbackQuery({ text: `Режим сна ${newState ? 'ВКЛЮЧЕН' : 'ВЫКЛЮЧЕН'}`, show_alert: true });
});

bot.callbackQuery('admin_broadcast', async (ctx) => {
  if (ctx.from.username !== ADMIN_USERNAME) return;
  await ctx.reply('Введите сообщение для рассылки:');
  ctx.session.step = 'admin_broadcast';
});

bot.on('message:text', async (ctx, next) => {
  if (ctx.session.step === 'admin_broadcast' && ctx.from.username === ADMIN_USERNAME) {
    const text = ctx.message.text;
    const usersSnap = await db.ref('users').once('value');
    const users = usersSnap.val() || {};
    
    let count = 0;
    for (const uid in users) {
      try {
        await bot.api.sendMessage(uid, `📢 <b>ОБЪЯВЛЕНИЕ:</b>\n\n${text}`, { parse_mode: 'HTML' });
        count++;
      } catch (e) {
        console.error(`Failed to send message to ${uid}`);
      }
    }
    
    await ctx.reply(`✅ Рассылка завершена. Отправлено ${count} пользователям.`);
    ctx.session.step = undefined;
    return;
  }
  return next();
});

bot.callbackQuery('admin_backup', async (ctx) => {
  if (ctx.from.username !== ADMIN_USERNAME) return;
  const data = await db.ref('/').once('value');
  const backup = JSON.stringify(data.val(), null, 2);
  // In a real bot we might send this as a file, but for now just a confirmation
  await ctx.answerCallbackQuery({ text: 'Бэкап данных выполнен (лог сервера)', show_alert: true });
  console.log('--- DATABASE BACKUP ---');
  console.log(backup);
});

bot.callbackQuery('admin_next', async (ctx) => {
  if (ctx.from.username !== ADMIN_USERNAME) return;
  await ctx.editMessageText('🛠 <b>Админ-панель (Стр. 2):</b>', {
    parse_mode: 'HTML',
    reply_markup: {
      inline_keyboard: [
        [
          { text: 'ОБНУЛИТЬ КАЗНУ (ВСЕ)', callback_data: 'admin_reset_gold' },
          { text: 'ТЕСТОВЫЙ РЕЖИМ', callback_data: 'admin_test_mode' }
        ],
        [
          { text: '⬅️ Назад', callback_data: 'admin_back' }
        ]
      ]
    }
  });
});

bot.callbackQuery('admin_back', async (ctx) => {
  if (ctx.from.username !== ADMIN_USERNAME) return;
  await ctx.editMessageText('🛠 <b>Админ-панель:</b>', {
    parse_mode: 'HTML',
    reply_markup: {
      inline_keyboard: [
        [
          { text: 'ВКЛ/ОТКЛ БОТА', callback_data: 'admin_toggle_bot' },
          { text: 'РЕЖИМ СНА', callback_data: 'admin_sleep' }
        ],
        [
          { text: 'РАССЫЛКА', callback_data: 'admin_broadcast' },
          { text: 'БЭКАП', callback_data: 'admin_backup' }
        ],
        [
          { text: '➡️ Далее', callback_data: 'admin_next' }
        ]
      ]
    }
  });
});

bot.callbackQuery('admin_reset_gold', async (ctx) => {
  if (ctx.from.username !== ADMIN_USERNAME) return;
  const clansSnap = await db.ref('clans').once('value');
  const clans = clansSnap.val() || {};
  
  for (const cid in clans) {
    await db.ref(`clans/${cid}`).update({ gold: 0 });
  }
  
  await ctx.answerCallbackQuery({ text: 'Казна всех кланов обнулена.', show_alert: true });
});

bot.callbackQuery('admin_test_mode', async (ctx) => {
  if (ctx.from.username !== ADMIN_USERNAME) return;
  const settings = await getSettings();
  const newState = !settings.test_mode;
  await db.ref('settings').update({ test_mode: newState });
  await ctx.answerCallbackQuery({ text: `Тестовый режим ${newState ? 'ВКЛЮЧЕН' : 'ВЫКЛЮЧЕН'}`, show_alert: true });
});

bot.command('разработка', async (ctx) => {
  const uid = ctx.from?.id.toString();
  const userSnap = await db.ref(`users/${uid}`).once('value');
  const user = userSnap.val();

  if (!user?.clan_id || user.role !== 'leader') {
    await ctx.reply('⚠️ Только лидер может заниматься разработкой ракет.');
    return;
  }

  await ctx.reply('🚀 <b>Ракетная программа:</b>\nВыберите тип ракеты для разработки:', {
    parse_mode: 'HTML',
    reply_markup: {
      inline_keyboard: [
        [
          { text: '🚀 Баллистическая (5000 золота, 1000 оружия)', callback_data: 'dev_ballistic' },
          { text: '☢️ Ядерная (25000 золота, 5000 оружия)', callback_data: 'dev_nuclear' }
        ]
      ]
    }
  });
});

bot.callbackQuery(/^dev_(ballistic|nuclear)$/, async (ctx) => {
  const type = ctx.match[1] as 'ballistic' | 'nuclear';
  const uid = ctx.from.id.toString();
  const userSnap = await db.ref(`users/${uid}`).once('value');
  const user = userSnap.val();

  if (!user?.clan_id || user.role !== 'leader') return;

  const clanRef = db.ref(`clans/${user.clan_id}`);
  const clanSnap = await clanRef.once('value');
  const clan = clanSnap.val();

  const goldPrice = type === 'ballistic' ? 5000 : 25000;
  const weaponPrice = type === 'ballistic' ? 1000 : 5000;

  if (clan.gold < goldPrice || clan.weapons < weaponPrice) {
    await ctx.answerCallbackQuery({ text: '❌ Недостаточно ресурсов.', show_alert: true });
    return;
  }

  const currentRockets = clan.rockets || { ballistics: 0, nuclear: 0 };
  const newRockets = { ...currentRockets };
  if (type === 'ballistic') newRockets.ballistics++;
  else newRockets.nuclear++;

  await clanRef.update({
    gold: clan.gold - goldPrice,
    weapons: clan.weapons - weaponPrice,
    rockets: newRockets
  });

  await ctx.editMessageText(`✅ Разработка завершена! У вас теперь ${newRockets.ballistics} баллистических и ${newRockets.nuclear} ядерных ракет.`);
});

bot.command('пуск', async (ctx) => {
  const args = ctx.match.split(' ');
  if (args.length < 2) {
    await ctx.reply('⚠️ Использование: <code>/пуск [тип: балл/ядер] [тег_клана]</code>', { parse_mode: 'HTML' });
    return;
  }

  const type = args[0].toLowerCase();
  const targetTag = args[1].toUpperCase();
  const uid = ctx.from?.id.toString();
  const userSnap = await db.ref(`users/${uid}`).once('value');
  const user = userSnap.val();

  if (!user?.clan_id || user.role !== 'leader') {
    await ctx.reply('⚠️ Только лидер может запускать ракеты.');
    return;
  }

  const clanRef = db.ref(`clans/${user.clan_id}`);
  const clanSnap = await clanRef.once('value');
  const clan = clanSnap.val();

  const rocketType = type.startsWith('балл') ? 'ballistics' : (type.startsWith('ядер') ? 'nuclear' : null);
  if (!rocketType || !clan.rockets || clan.rockets[rocketType] <= 0) {
    await ctx.reply('⚠️ У вас нет таких ракет.');
    return;
  }

  const clansSnap = await db.ref('clans').once('value');
  const clans = clansSnap.val() || {};
  let targetId = null;
  for (const cid in clans) {
    if (clans[cid].tag === targetTag) {
      targetId = cid;
      break;
    }
  }

  if (!targetId || targetId === user.clan_id) {
    await ctx.reply('⚠️ Неверный тег клана.');
    return;
  }

  const targetClan = clans[targetId];
  const damage = rocketType === 'ballistics' ? 200 : 1000;
  const newHp = Math.max(0, targetClan.hp - damage);

  await db.ref(`clans/${targetId}`).update({ hp: newHp });
  await clanRef.update({ [`rockets/${rocketType}`]: clan.rockets[rocketType] - 1 });

  await ctx.reply(`🚀 РАКЕТА ЗАПУЩЕНА! Клан ${targetClan.name} получил ${damage} урона. Осталось HP: ${newHp}`);
});
bot.command('война', async (ctx) => {
  const args = ctx.match.split(' ');
  if (args.length < 2 || args[0].toLowerCase() !== 'объявить') {
    await ctx.reply('⚠️ Использование: <code>/война объявить [тег_клана]</code>', { parse_mode: 'HTML' });
    return;
  }

  const targetTag = args[1].toUpperCase();
  const uid = ctx.from?.id.toString();
  const userSnap = await db.ref(`users/${uid}`).once('value');
  const user = userSnap.val();

  if (!user?.clan_id || user.role !== 'leader') {
    await ctx.reply('⚠️ Только лидер может объявлять войну.');
    return;
  }

  const clansSnap = await db.ref('clans').once('value');
  const clans = clansSnap.val() || {};
  
  let targetId = null;
  for (const cid in clans) {
    if (clans[cid].tag === targetTag) {
      targetId = cid;
      break;
    }
  }

  if (!targetId || targetId === user.clan_id) {
    await ctx.reply('⚠️ Неверный тег клана.');
    return;
  }

  await db.ref(`clans/${user.clan_id}/war`).set({
    target_id: targetId,
    start_time: Date.now(),
    status: 'active'
  });

  await ctx.reply(`⚔️ Клан ${clans[user.clan_id].name} объявил войну клану ${clans[targetId].name}!`);
});

// --- HOURLY INCOME ---

setInterval(async () => {
  console.log('Running hourly production...');
  const clansSnap = await db.ref('clans').once('value');
  const clans = clansSnap.val() || {};

  for (const cid in clans) {
    const clan = clans[cid];
    let goldIncome = 0;
    let weaponIncome = 0;

    if (clan.factories) {
      for (const fid in clan.factories) {
        const factory = clan.factories[fid];
        if (factory.type === 'finance') {
          goldIncome += 100 * factory.level;
        } else if (factory.type === 'weapon') {
          weaponIncome += 50 * factory.level;
        }
      }
    }

    if (goldIncome > 0 || weaponIncome > 0) {
      await db.ref(`clans/${cid}`).update({
        gold: (clan.gold || 0) + goldIncome,
        weapons: (clan.weapons || 0) + weaponIncome
      });
    }
  }
}, 3600000); // 1 hour

bot.command('инфо', async (ctx) => {
  const clansSnap = await db.ref('clans').once('value');
  const usersSnap = await db.ref('users').once('value');
  const clans = clansSnap.val() || {};
  const users = usersSnap.val() || {};

  const text = `ℹ️ <b>Информация о боте:</b>\n\n` +
    `🏰 Всего кланов: ${Object.keys(clans).length}\n` +
    `👥 Всего игроков: ${Object.keys(users).length}\n` +
    `🚀 Ракет в мире: ${Object.values(clans).reduce((acc: number, c: any) => acc + (c.rockets?.ballistics || 0) + (c.rockets?.nuclear || 0), 0)}`;

  await ctx.reply(text, { parse_mode: 'HTML' });
});

bot.command('назначить', async (ctx) => {
  const uid = ctx.from?.id.toString();
  const userSnap = await db.ref(`users/${uid}`).once('value');
  const user = userSnap.val();

  if (!user?.clan_id || user.role !== 'leader') {
    await ctx.reply('⚠️ Только лидер может назначать роли.');
    return;
  }

  const args = ctx.match.split(' ');
  if (args.length < 2) {
    await ctx.reply('⚠️ Использование: <code>/назначить [username] [роль: зам/офицер]</code>', { parse_mode: 'HTML' });
    return;
  }

  const targetUsername = args[0].replace('@', '');
  const role = args[1].toLowerCase() === 'зам' ? 'deputy' : 'officer';

  // Find user by username
  const usersSnap = await db.ref('users').once('value');
  const users = usersSnap.val() || {};
  let targetId = null;
  for (const id in users) {
    if (users[id].username === targetUsername && users[id].clan_id === user.clan_id) {
      targetId = id;
      break;
    }
  }

  if (!targetId) {
    await ctx.reply('⚠️ Пользователь не найден в вашем клане.');
    return;
  }

  await db.ref(`users/${targetId}`).update({ role });
  await ctx.reply(`✅ Пользователь @${targetUsername} назначен на роль ${role === 'deputy' ? 'Заместитель' : 'Офицер'}.`);
});

bot.command('мобилизация', async (ctx) => {
  const uid = ctx.from?.id.toString();
  const userSnap = await db.ref(`users/${uid}`).once('value');
  const user = userSnap.val();

  if (!user?.clan_id || user.role !== 'leader') {
    await ctx.reply('⚠️ Только лидер может проводить мобилизацию.');
    return;
  }

  const clanRef = db.ref(`clans/${user.clan_id}`);
  const clanSnap = await clanRef.once('value');
  const clan = clanSnap.val();

  const cost = 1000;
  if (clan.gold < cost) {
    await ctx.reply('❌ Недостаточно золота для мобилизации (нужно 1000).');
    return;
  }

  const newArmyCount = (clan.army?.count || 0) + 100;
  await clanRef.update({
    gold: clan.gold - cost,
    'army/count': newArmyCount
  });

  await ctx.reply(`🎖 Мобилизация проведена! Нанято 100 солдат. Всего в армии: ${newArmyCount}`);
});

bot.command('атака', async (ctx) => {
  const uid = ctx.from?.id.toString();
  const userSnap = await db.ref(`users/${uid}`).once('value');
  const user = userSnap.val();

  if (!user?.clan_id) {
    await ctx.reply('⚠️ Вы не в клане.');
    return;
  }

  const clanRef = db.ref(`clans/${user.clan_id}`);
  const clanSnap = await clanRef.once('value');
  const clan = clanSnap.val();

  if (!clan.war || clan.war.status !== 'active') {
    await ctx.reply('⚠️ Ваш клан не находится в состоянии войны.');
    return;
  }

  const targetId = clan.war.target_id;
  const targetSnap = await db.ref(`clans/${targetId}`).once('value');
  const target = targetSnap.val();

  if (!target) {
    await ctx.reply('⚠️ Цель войны не найдена.');
    return;
  }

  // Simple attack logic
  const myStrength = (clan.army?.count || 0) * 10 + (clan.weapons || 0);
  const targetStrength = (target.army?.count || 0) * 10 + (target.weapons || 0);

  const damage = Math.max(10, Math.floor(myStrength / 10));
  const newTargetHp = Math.max(0, target.hp - damage);

  await db.ref(`clans/${targetId}`).update({ hp: newTargetHp });
  
  if (newTargetHp === 0) {
    await ctx.reply(`🔥 ПОБЕДА! Клан ${target.name} капитулировал!`);
    await clanRef.child('war').remove();
    await db.ref(`clans/${targetId}/war`).remove();
  } else {
    await ctx.reply(`⚔️ Вы атаковали клан ${target.name}! Нанесено ${damage} урона. Осталось HP: ${newTargetHp}`);
  }
});

// bot.start();
// console.log('Bot is running...');
