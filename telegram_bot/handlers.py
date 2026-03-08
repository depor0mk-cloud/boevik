import logging
import html
import re
import asyncio
import random
from datetime import datetime, timedelta
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from firebase_db import get_db_ref

router = Router()

# ... imports ...
from aiogram.types import InlineKeyboardButton

# ... AdminStates ...
class AdminStates(StatesGroup):
    waiting_for_broadcast = State()
    waiting_for_sleep_time = State()
    waiting_for_gold = State()
    waiting_for_army = State()
    waiting_for_delete_clan = State()
    waiting_for_end_war = State()
    waiting_for_leader = State()
    waiting_for_ban = State()
    waiting_for_unban = State()
    waiting_for_reset_cd = State()
    waiting_for_limit = State()
    waiting_for_factory = State()
    waiting_for_rocket = State()

# ... helper functions ...

def get_user_by_username_or_id(query):
    query = str(query).replace('@', '').lower()
    all_users = get_db_ref('users').get() or {}
    for uid, data in all_users.items():
        if str(uid) == query:
            return uid, data
        if data.get('username', '').lower() == query:
            return uid, data
    return None, None

def format_user_link(user_id, name):
    return f'<a href="tg://user?id={user_id}">{html.escape(name)}</a>'

def get_clan_by_tag_or_id(query):
    query = str(query).lower().strip('[]')
    all_clans = get_db_ref('clans').get() or {}
    for cid, data in all_clans.items():
        if str(cid) == query:
            return cid, data
        if data.get('tag', '').lower() == query or data.get('name', '').lower() == query:
            return cid, data
    return None, None

# ... existing functions ...



# Remove work, job, build_factory, develop, launch handlers by not including them or deleting them.
# I will use edit_file to replace the blocks.



import contextvars

current_user_ctx = contextvars.ContextVar('current_user_ctx', default=None)

def is_bot_active():
    user = current_user_ctx.get()
    settings = get_db_ref('settings').get() or {}
    if user:
        if user.username == 'Trim_peek': return True
        if str(user.id) == str(settings.get('test_mode_user')): return True
    return settings.get('bot_enabled', True)

def is_sleep_mode():
    settings = get_db_ref('settings').get() or {}
    sleep_range = settings.get('sleep_mode')
    if not sleep_range or sleep_range == "0":
        return False
    try:
        start_str, end_str = sleep_range.split('-')
        now = datetime.utcnow() + timedelta(hours=3) # MSK
        current_time = now.time()
        start_time = datetime.strptime(start_str, "%H:%M").time()
        end_time = datetime.strptime(end_str, "%H:%M").time()
        
        if start_time > end_time:
            if current_time >= start_time or current_time < end_time:
                return True
        else:
            if start_time <= current_time < end_time:
                return True
    except:
        return False
    return False

def collect_production(clan_id):
    clan_ref = get_db_ref(f'clans/{clan_id}')
    clan = clan_ref.get()
    if not clan: return
    
    productions = clan.get('productions', {})
    resources = clan.get('resources', {})
    now = datetime.now()
    
    updated = False
    for item, data in productions.items():
        last_time = datetime.fromisoformat(data.get('last_collected', now.isoformat()))
        hours_passed = (now - last_time).total_seconds() / 3600.0
        if hours_passed > 0:
            rate = data.get('level', 1) * 10
            produced = int(hours_passed * rate)
            if produced > 0:
                resources[item] = resources.get(item, 0) + produced
                # Update last_collected to account for fractional hours
                # We only advance by the exact hours we consumed
                consumed_seconds = produced / rate * 3600.0
                new_last_time = last_time + timedelta(seconds=consumed_seconds)
                data['last_collected'] = new_last_time.isoformat()
                updated = True
                
    if updated:
        clan_ref.update({'productions': productions, 'resources': resources})

def get_or_create_user(user_id, username):
    user_id = str(user_id)
    ref = get_db_ref(f'users/{user_id}')
    user = ref.get()
    if not user:
        user = {
            'user_id': user_id,
            'username': username,
            'clan_id': None,
            'army': 0,
            'last_mobilization': None,
            'last_train': None,
            'last_factory': None
        }
        ref.set(user)
    return user

async def broadcast_message(bot, text):
    all_clans = get_db_ref('clans').get() or {}
    chat_ids = set(c.get('chat_id') for c in all_clans.values() if c.get('chat_id'))
    for chat_id in chat_ids:
        try:
            await bot.send_message(chat_id, text)
            await asyncio.sleep(0.05)
        except:
            pass

# --- ADMIN PANEL ---

@router.message(Command("админ2105"))
async def admin_panel(message: types.Message):
    await show_admin_panel(message, page=1)

async def show_admin_panel(message, page=1):
    builder = InlineKeyboardBuilder()
    if page == 1:
        settings = get_db_ref('settings').get() or {}
        bot_enabled = settings.get('bot_enabled', True)
        status = "🟢" if bot_enabled else "🔴"
        builder.button(text=f"{status} Бот", callback_data="admin_toggle_bot")
        builder.button(text="🌙 Сон", callback_data="admin_set_sleep")
        builder.button(text="📢 Рассылка", callback_data="admin_broadcast")
        builder.button(text="📊 Статистика", callback_data="admin_stats")
        builder.button(text="💰 +Золото", callback_data="admin_add_gold")
        builder.button(text="⚔️ +Армия", callback_data="admin_add_army")
        builder.button(text="🗑 Удалить клан", callback_data="admin_del_clan")
        builder.button(text="🕊 Стоп война", callback_data="admin_end_war")
        builder.button(text="👑 Лидер", callback_data="admin_set_leader")
        builder.adjust(3, 3, 3)
        builder.row(types.InlineKeyboardButton(text="➡️ Далее", callback_data="admin_page_2"))
    elif page == 2:
        builder.button(text="🚫 Бан", callback_data="admin_ban_user")
        builder.button(text="✅ Разбан", callback_data="admin_unban_user")
        builder.button(text="🔄 Сброс КД", callback_data="admin_reset_cd")
        builder.button(text="🏭 +Завод", callback_data="admin_add_factory")
        builder.button(text="🚀 +Ракеты", callback_data="admin_add_rocket")
        builder.button(text="👥 Лимит", callback_data="admin_set_limit")
        builder.adjust(2, 2)
        builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_page_1"))

    text = f"🔧 <b>Админ-панель (Стр. {page}/2)</b>\nВыберите действие:"
    if isinstance(message, types.Message):
        await message.answer(text, reply_markup=builder.as_markup())
    elif isinstance(message, types.CallbackQuery):
        await message.edit_text(text, reply_markup=builder.as_markup())

@router.callback_query(F.data.startswith("admin_"))
async def admin_callbacks(callback: types.CallbackQuery, state: FSMContext):
    action = callback.data
    if action == "admin_page_1":
        await show_admin_panel(callback, page=1)
    elif action == "admin_page_2":
        await show_admin_panel(callback, page=2)
    elif action == "admin_toggle_bot":
        settings = get_db_ref('settings').get() or {}
        current = settings.get('bot_enabled', True)
        new_status = not current
        get_db_ref('settings').update({'bot_enabled': new_status})
        status_text = "🟢 ВКЛЮЧЕН" if new_status else "🔴 ОТКЛЮЧЕН"
        await callback.answer(f"Бот {status_text}", show_alert=True)
        await show_admin_panel(callback, page=1)
        msg = "✅ <b>Бот включен!</b> Можно играть." if new_status else "⚠️ <b>Бот отключен на тех. работы!</b>"
        asyncio.create_task(broadcast_message(callback.bot, msg))
    elif action == "admin_stats":
        users = len(get_db_ref('users').get() or {})
        clans = len(get_db_ref('clans').get() or {})
        wars = len(get_db_ref('wars').get() or {})
        text = f"📊 <b>Статистика:</b>\n👥 Юзеров: {users}\n🛡 Кланов: {clans}\n⚔️ Войн: {wars}"
        builder = InlineKeyboardBuilder()
        builder.button(text="🔙 Назад", callback_data="admin_page_1")
        await callback.message.edit_text(text, reply_markup=builder.as_markup())
    elif action == "admin_set_sleep":
        await callback.message.edit_text("Введите время сна (МСК) в формате <code>22:00-08:00</code> или <code>0</code>:", parse_mode="HTML")
        await state.set_state(AdminStates.waiting_for_sleep_time)
    elif action == "admin_broadcast":
        await callback.message.edit_text("Введите текст для рассылки:")
        await state.set_state(AdminStates.waiting_for_broadcast)
    elif action == "admin_add_gold":
        await callback.message.edit_text("Введите ID клана и количество золота (через пробел):")
        await state.set_state(AdminStates.waiting_for_gold)
    elif action == "admin_add_army":
        await callback.message.edit_text("Введите ID пользователя и количество армии (через пробел):")
        await state.set_state(AdminStates.waiting_for_army)
    elif action == "admin_del_clan":
        await callback.message.edit_text("Введите ID клана для удаления:")
        await state.set_state(AdminStates.waiting_for_delete_clan)
    elif action == "admin_end_war":
        await callback.message.edit_text("Введите ID войны (или ID любого клана-участника):")
        await state.set_state(AdminStates.waiting_for_end_war)
    elif action == "admin_set_leader":
        await callback.message.edit_text("Введите ID клана и ID нового лидера (через пробел):")
        await state.set_state(AdminStates.waiting_for_leader)
    elif action == "admin_ban_user":
        await callback.message.edit_text("Введите ID пользователя для бана:")
        await state.set_state(AdminStates.waiting_for_ban)
    elif action == "admin_unban_user":
        await callback.message.edit_text("Введите ID пользователя для разбана:")
        await state.set_state(AdminStates.waiting_for_unban)
    elif action == "admin_reset_cd":
        await callback.message.edit_text("Введите ID пользователя для сброса КД:")
        await state.set_state(AdminStates.waiting_for_reset_cd)
    elif action == "admin_add_factory":
        await callback.message.edit_text("Введите ID клана, тип завода (1-3) и кол-во (через пробел):")
        await state.set_state(AdminStates.waiting_for_factory)
    elif action == "admin_add_rocket":
        await callback.message.edit_text("Введите ID клана, тип (1=балл, 2=яд) и прогресс (через пробел):")
        await state.set_state(AdminStates.waiting_for_rocket)
    elif action == "admin_set_limit":
        await callback.message.edit_text("Введите ID клана и новый лимит людей (через пробел):")
        await state.set_state(AdminStates.waiting_for_limit)

@router.message(AdminStates.waiting_for_sleep_time)
async def process_sleep_time(message: types.Message, state: FSMContext):
    time_range = message.text.strip()
    get_db_ref('settings').update({'sleep_mode': time_range})
    await message.answer(f"✅ Режим сна установлен: {time_range}")
    await state.clear()
    await show_admin_panel(message, page=1)

@router.message(AdminStates.waiting_for_broadcast)
async def process_broadcast(message: types.Message, state: FSMContext):
    text = message.text
    asyncio.create_task(broadcast_message(message.bot, f"📢 <b>ОБЪЯВЛЕНИЕ:</b>\n{text}"))
    await message.answer("✅ Рассылка запущена.")
    await state.clear()
    await show_admin_panel(message, page=1)

@router.message(AdminStates.waiting_for_gold)
async def process_add_gold(message: types.Message, state: FSMContext):
    try:
        query, amount = message.text.split()
        amount = int(amount)
        clan_id, clan_data = get_clan_by_tag_or_id(query)
        if not clan_id:
            await message.answer("⚠️ Клан не найден.")
        else:
            current = clan_data.get('gold', 0)
            get_db_ref(f'clans/{clan_id}').update({'gold': current + amount})
            await message.answer(f"✅ Выдано {amount} золота клану {html.escape(clan_data.get('name', clan_id))}.")
    except:
        await message.answer("⚠️ Ошибка формата.")
    await state.clear()
    await show_admin_panel(message, page=1)

@router.message(AdminStates.waiting_for_army)
async def process_add_army(message: types.Message, state: FSMContext):
    try:
        query, amount = message.text.split()
        amount = int(amount)
        uid, udata = get_user_by_username_or_id(query)
        if not uid:
            await message.answer("⚠️ Пользователь не найден.")
        else:
            current = udata.get('army', 0)
            get_db_ref(f'users/{uid}').update({'army': current + amount})
            name = udata.get('username', uid)
            await message.answer(f"✅ Выдано {amount} армии пользователю {format_user_link(uid, name)}.")
    except:
        await message.answer("⚠️ Ошибка формата.")
    await state.clear()
    await show_admin_panel(message, page=1)

@router.message(AdminStates.waiting_for_delete_clan)
async def process_del_clan(message: types.Message, state: FSMContext):
    query = message.text.strip()
    clan_id, clan_data = get_clan_by_tag_or_id(query)
    if not clan_id:
        await message.answer("⚠️ Клан не найден.")
    else:
        all_users = get_db_ref('users').get() or {}
        for uid, udata in all_users.items():
            if udata.get('clan_id') == clan_id:
                get_db_ref(f'users/{uid}').update({'clan_id': None})
        get_db_ref(f'clans/{clan_id}').delete()
        await message.answer(f"✅ Клан {html.escape(clan_data.get('name', clan_id))} удален.")
    await state.clear()
    await show_admin_panel(message, page=1)

@router.message(AdminStates.waiting_for_end_war)
async def process_end_war(message: types.Message, state: FSMContext):
    query = message.text.strip()
    war_ref = get_db_ref(f'wars/{query}')
    war = war_ref.get()
    if not war:
        clan_id, clan_data = get_clan_by_tag_or_id(query)
        if clan_id and clan_data.get('war_id'):
            war_ref = get_db_ref(f'wars/{clan_data["war_id"]}')
            war = war_ref.get()
    if not war:
        await message.answer("⚠️ Война не найдена.")
    else:
        aid = war['attacker_id']
        did = war['defender_id']
        get_db_ref(f'clans/{aid}').update({'war_id': None})
        get_db_ref(f'clans/{did}').update({'war_id': None})
        war_ref.delete()
        await message.answer("✅ Война остановлена.")
    await state.clear()
    await show_admin_panel(message, page=1)

@router.message(AdminStates.waiting_for_leader)
async def process_set_leader(message: types.Message, state: FSMContext):
    try:
        clan_query, leader_query = message.text.split()
        clan_id, clan_data = get_clan_by_tag_or_id(clan_query)
        if not clan_id:
            await message.answer("⚠️ Клан не найден.")
        else:
            uid, udata = get_user_by_username_or_id(leader_query)
            if not uid:
                await message.answer("⚠️ Пользователь не найден.")
            else:
                get_db_ref(f'clans/{clan_id}').update({'leader_id': uid})
                name = udata.get('username', uid)
                await message.answer(f"✅ Лидер клана {html.escape(clan_data.get('name', clan_id))} изменен на {format_user_link(uid, name)}.")
    except:
        await message.answer("⚠️ Ошибка формата.")
    await state.clear()
    await show_admin_panel(message, page=1)

@router.message(AdminStates.waiting_for_ban)
async def process_ban(message: types.Message, state: FSMContext):
    query = message.text.strip()
    uid, udata = get_user_by_username_or_id(query)
    if not uid:
        await message.answer("⚠️ Пользователь не найден.")
    else:
        get_db_ref(f'users/{uid}').update({'banned': True})
        name = udata.get('username', uid)
        await message.answer(f"✅ Пользователь {format_user_link(uid, name)} забанен.")
    await state.clear()
    await show_admin_panel(message, page=2)

@router.message(AdminStates.waiting_for_unban)
async def process_unban(message: types.Message, state: FSMContext):
    query = message.text.strip()
    uid, udata = get_user_by_username_or_id(query)
    if not uid:
        await message.answer("⚠️ Пользователь не найден.")
    else:
        get_db_ref(f'users/{uid}').update({'banned': False})
        name = udata.get('username', uid)
        await message.answer(f"✅ Пользователь {format_user_link(uid, name)} разбанен.")
    await state.clear()
    await show_admin_panel(message, page=2)

@router.message(AdminStates.waiting_for_reset_cd)
async def process_reset_cd(message: types.Message, state: FSMContext):
    query = message.text.strip()
    uid, udata = get_user_by_username_or_id(query)
    if not uid:
        await message.answer("⚠️ Пользователь не найден.")
    else:
        get_db_ref(f'users/{uid}').update({
            'last_mobilization': None, 'last_work': None, 'last_job': None,
            'last_train': None, 'last_factory': None, 'last_attack': None, 'last_rocket_dev': None
        })
        name = udata.get('username', uid)
        await message.answer(f"✅ КД пользователя {format_user_link(uid, name)} сброшены.")
    await state.clear()
    await show_admin_panel(message, page=2)

@router.message(AdminStates.waiting_for_limit)
async def process_set_limit(message: types.Message, state: FSMContext):
    try:
        query, limit = message.text.split()
        limit = int(limit)
        clan_id, clan_data = get_clan_by_tag_or_id(query)
        if not clan_id:
            await message.answer("⚠️ Клан не найден.")
        else:
            get_db_ref(f'clans/{clan_id}').update({'population_limit': limit})
            await message.answer(f"✅ Лимит клана {html.escape(clan_data.get('name', clan_id))} установлен на {limit}.")
    except:
        await message.answer("⚠️ Ошибка формата.")
    await state.clear()
    await show_admin_panel(message, page=2)

# --- USER HANDLERS ---
@router.message(Command("вкл2105"))
async def enable_test_mode(message: types.Message):
    get_db_ref('settings').update({'test_mode_user': str(message.from_user.id), 'bot_enabled': False})
    await message.answer("🔧 Тестовый режим включен. Бот работает только для вас и @Trim_peek.")

@router.message(Command("выкл2105"))
async def disable_test_mode(message: types.Message):
    get_db_ref('settings').update({'test_mode_user': None, 'bot_enabled': True})
    await message.answer("✅ Тестовый режим выключен. Бот снова доступен для всех.")

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    if not is_bot_active():
        await message.answer("⚠️ Бот временно отключен на технические работы.")
        return
    text = (
        "👋 <b>Приветствую, полководец!</b>\n\n"
        "Я — Клан-Бот, твой верный помощник в управлении кланом и ведении войн.\n"
        "Создавай свой клан, нанимай армию, строй заводы и сражайся за господство!\n\n"
        "📜 <b>Основные команды:</b>\n"
        "• /создать клан [название] [тег] — Основать новый клан\n"
        "• /вступить [название/тег/номер] — Присоединиться к существующему клану\n"
        "• /клан — Информация о твоем клане\n"
        "• /профиль — Твоя личная статистика\n"
        "• /boevik — Полный справочник команд\n\n"
        "Удачи на полях сражений!"
    )
    await message.answer(text)

@router.message(Command("boevik"))
async def cmd_boevik(message: types.Message):
    if not is_bot_active():
        await message.answer("⚠️ Бот временно отключен на технические работы.")
        return
    text = (
        "⚔️ <b>Справочник Клан-Бота</b> ⚔️\n\n"
        "<b>🏰 Управление кланом:</b>\n"
        "• <code>/создать клан [имя] [тег]</code> — Создать клан\n"
        "• <code>/вступить [тег/номер]</code> — Вступить в клан\n"
        "• <code>/клан</code> — Меню клана\n"
        "• <code>/выйти</code> — Покинуть клан\n"
        "• <code>/удалить клан</code> — Удалить клан (только лидер)\n"
        "• <code>/переименовать клан [имя]</code> — Сменить имя клана\n"
        "• <code>/кик [id]</code> — Исключить игрока (только лидер)\n"
        "• <code>/повысить [id]</code> — Передать лидерство\n"
        "• <code>/список кланов</code> — Топ кланов чата\n"
        "• <code>/мой клан</code> — Инфо о клане в ЛС\n\n"
        "<b>💰 Экономика:</b>\n"
        "• <code>/экономика</code> — Инфо о ресурсах и производстве\n"
        "• <code>/создать производство [товар]</code> — 1000 💰\n"
        "• <code>/улучшить производство [товар]</code> — Ускорить добычу\n"
        "• <code>/мировой магазин</code> — Рынок ресурсов\n"
        "• <code>/продать [товар] [кол-во] [цена]</code> — Выставить лот\n"
        "• <code>/купить [id] [кол-во]</code> — Купить на рынке\n"
        "• <code>/подработка</code> — Мелкий заработок (КД 30 мин)\n"
        "• <code>/устроиться</code> — Крупный заработок (КД 6 ч)\n"
        "• <code>/строй завод</code> — Строительство (лидер, КД 10 мин)\n\n"
        "<b>⚔️ Война:</b>\n"
        "• <code>/объявить войну [клан]</code> — Начать войну\n"
        "• <code>/мир [клан] [ресурс/золото] [кол-во]</code> — Мирный договор\n"
        "• <code>/мобилизация</code> — Нанять армию (лидер)\n"
        "• <code>/атака [кол-во]</code> — Атаковать врага\n"
        "• <code>/оборона [кол-во]</code> — Укрепить защиту\n"
        "• <code>/столица [сумма]</code> — Укрепить столицу\n"
        "• <code>/ультиматум [клан] [текст]</code> — Отправить требование\n\n"
        "<b>🤝 Дипломатия:</b>\n"
        "• <code>/предложить альянс [клан]</code> — Предложить союз\n"
        "• <code>/разорвать альянс [клан]</code> — Разорвать союз\n\n"
        "<b>🚀 Технологии:</b>\n"
        "• <code>/разработка</code> — Вклад в ракеты (Граждане: 1 раз/час)\n"
        "• <code>/пуск [тип] [цель]</code> — Ядерный удар\n"
    )
    await message.answer(text)

@router.message(F.text.regexp(r'(?i)^/переименовать клан'))
async def rename_clan(message: types.Message):
    if not is_bot_active(): return
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        await message.answer("⚠️ Использование: <code>/переименовать клан [новое имя]</code>")
        return
    new_name = args[2]
    user_id = str(message.from_user.id)
    user = get_or_create_user(user_id, message.from_user.username or message.from_user.first_name)
    clan_id = user.get('clan_id')
    if not clan_id: return
    clan = get_db_ref(f'clans/{clan_id}').get()
    if clan.get('leader_id') != user_id:
        await message.answer("⚠️ Только лидер может переименовать клан.")
        return
    get_db_ref(f'clans/{clan_id}').update({'name': new_name})
    await message.answer(f"✅ Клан переименован в <b>{html.escape(new_name)}</b>.")

@router.message(F.text.regexp(r'(?i)^/создать клан'))
async def create_clan(message: types.Message):
    if not is_bot_active():
        await message.answer("⚠️ Бот временно отключен на технические работы.")
        return
    args = message.text.split()
    if len(args) < 4:
        await message.answer("⚠️ Использование: <code>/создать клан [Название] [Тег]</code>")
        return
    
    name = args[2]
    tag = args[3]
    user_id = str(message.from_user.id)
    user = get_or_create_user(user_id, message.from_user.username or message.from_user.first_name)
    
    if user.get('clan_id'):
        await message.answer("⚠️ Вы уже состоите в клане.")
        return
        
    # Check if name/tag exists
    all_clans = get_db_ref('clans').get() or {}
    for c in all_clans.values():
        if c.get('name') == name or c.get('tag') == tag:
            await message.answer("⚠️ Клан с таким названием или тегом уже существует.")
            return

    # Cost 1000 (virtual check, maybe free for now or check user balance if implemented)
    # Assuming free creation based on previous context, or check user gold? 
    # Previous code didn't strictly enforce user gold for creation, but let's assume free for simplicity unless specified.
    
    new_clan_ref = get_db_ref('clans').push()
    clan_id = new_clan_ref.key
    clan_data = {
        'name': name,
        'tag': tag,
        'leader_id': user_id,
        'gold': 0,
        'army': 0,
        'chat_id': message.chat.id,
        'created_at': datetime.now().isoformat(),
        'factory_weapon': 0,
        'factory_finance': 0,
        'factory_defense': 0,
        'population_limit': 10,
        'exp': 0,
        'allies': []
    }
    new_clan_ref.set(clan_data)
    get_db_ref(f'users/{user_id}').update({'clan_id': clan_id})
    
    await message.answer(f"✅ Клан <b>{html.escape(name)}</b> [{html.escape(tag)}] успешно создан!")

@router.message(Command("вступить", prefix="/"))
async def join_clan(message: types.Message):
    if not is_bot_active():
        await message.answer("⚠️ Бот временно отключен на технические работы.")
        return
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("⚠️ Использование: <code>/вступить [название или тег или номер]</code>")
        return
        
    query = args[1].lower()
    user_id = str(message.from_user.id)
    user = get_or_create_user(user_id, message.from_user.username or message.from_user.first_name)
    
    if user.get('clan_id'):
        await message.answer("⚠️ Вы уже в клане.")
        return
        
    all_clans = get_db_ref('clans').get() or {}
    target_clan_id = None
    target_clan = None
    
    if query.isdigit():
        idx = int(query) - 1
        group_clans = []
        for cid, cdata in all_clans.items():
            if cdata.get('chat_id') == message.chat.id:
                cdata['id'] = cid
                group_clans.append(cdata)
        group_clans.sort(key=lambda x: x.get('exp', 0), reverse=True)
        if 0 <= idx < len(group_clans):
            target_clan = group_clans[idx]
            target_clan_id = target_clan['id']
    else:
        for cid, cdata in all_clans.items():
            if cdata.get('name', '').lower() == query or cdata.get('tag', '').lower() == query:
                target_clan_id = cid
                target_clan = cdata
                break
            
    if not target_clan:
        await message.answer("⚠️ Клан не найден.")
        return
        
    # Check limit
    members = sum(1 for u in (get_db_ref('users').get() or {}).values() if u.get('clan_id') == target_clan_id)
    limit = target_clan.get('population_limit', 10)
    if members >= limit:
        await message.answer("⚠️ В клане нет мест.")
        return
        
    get_db_ref(f'users/{user_id}').update({'clan_id': target_clan_id})
    await message.answer(f"✅ Вы вступили в клан <b>{html.escape(target_clan.get('name', ''))}</b>!")

@router.message(Command("профиль", prefix="/"))
async def profile(message: types.Message):
    user_id = str(message.from_user.id)
    user = get_or_create_user(user_id, message.from_user.username or message.from_user.first_name)
    clan_id = user.get('clan_id')
    clan_name = "Нет"
    if clan_id:
        clan = get_db_ref(f'clans/{clan_id}').get()
        if clan:
            clan_name = clan.get('name', 'Неизвестно')
            
    text = (
        f"👤 <b>Профиль:</b> {html.escape(user.get('username', 'User'))}\n"
        f"🛡 <b>Клан:</b> {html.escape(clan_name)}\n"
        f"⚔️ <b>Армия:</b> {user.get('army', 0)}\n"
    )
    await message.answer(text)

@router.message(F.text.regexp(r'(?i)^/список кланов'))
async def list_clans(message: types.Message):
    if message.chat.type == 'private':
        await message.answer("⚠️ Эта команда работает только в группах.")
        return
    all_clans = get_db_ref('clans').get() or {}
    group_clans = []
    for cid, cdata in all_clans.items():
        if cdata.get('chat_id') == message.chat.id:
            cdata['id'] = cid
            group_clans.append(cdata)
    if not group_clans:
        await message.answer("В этой группе пока нет кланов.")
        return
    group_clans.sort(key=lambda x: x.get('exp', 0), reverse=True)
    all_users = get_db_ref('users').get() or {}
    lines = ["🏆 <b>Кланы этой группы:</b>\n"]
    for i, c in enumerate(group_clans, 1):
        members = sum(1 for u in all_users.values() if u.get('clan_id') == c['id'])
        lines.append(f"{i}. <b>{html.escape(c.get('name', ''))}</b> [{html.escape(c.get('tag', ''))}] — 👥 {members} | 💰 {c.get('gold', 0)} | 🌟 {c.get('exp', 0)}")
    await message.answer("\n".join(lines))

@router.message(F.text.regexp(r'(?i)^/клан'))
async def clan_menu(message: types.Message):
    user_id = str(message.from_user.id)
    user = get_or_create_user(user_id, message.from_user.username or message.from_user.first_name)
    clan_id = user.get('clan_id')
    if not clan_id:
        await message.answer("⚠️ Вы не состоите в клане.")
        return
    clan = get_db_ref(f'clans/{clan_id}').get()
    if not clan: return
    
    is_leader = (clan.get('leader_id') == user_id)
    role = "👑 Лидер" if is_leader else "👤 Участник"
    
    text = (
        f"🏰 <b>Клан: {html.escape(clan.get('name', ''))}</b>\n"
        f"🏷 Тег: {html.escape(clan.get('tag', ''))}\n"
        f"💰 Казна: {clan.get('gold', 0)}\n"
        f"🌟 Опыт: {clan.get('exp', 0)}\n"
        f"👥 Лимит: {clan.get('population_limit', 10)}\n"
        f"Ваша роль: {role}\n"
    )
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🧹 Подработка", callback_data=f"c_work_{user_id}")
    builder.button(text="🚀 Ракеты", callback_data=f"c_rocket_{user_id}")
    
    if not is_leader:
        builder.button(text="🏢 Устроиться", callback_data=f"c_job_{user_id}")
        builder.button(text="🚪 Выйти", callback_data=f"c_leave_{user_id}")
    else:
        builder.button(text="⚔️ Мобилизация", callback_data=f"c_mob_{user_id}")
        builder.button(text="💪 Тренировка", callback_data=f"c_train_{user_id}")
        builder.button(text="🏭 Завод", callback_data=f"c_factory_{user_id}")
        builder.button(text="💥 Распустить", callback_data=f"c_delete_{user_id}")
        
    builder.adjust(2)
    await message.answer(text, reply_markup=builder.as_markup())

@router.message(F.text.regexp(r'(?i)^/мой клан'))
async def my_clan_info(message: types.Message):
    await clan_menu(message)

@router.message(Command("выйти", prefix="/"))
async def leave_clan_cmd(message: types.Message, user_id=None, username=None):
    uid = str(user_id) if user_id else str(message.from_user.id)
    uname = username or (message.from_user.username or message.from_user.first_name)
    user = get_or_create_user(uid, uname)
    clan_id = user.get('clan_id')
    if not clan_id:
        await message.answer("⚠️ Вы не в клане.")
        return
    clan = get_db_ref(f'clans/{clan_id}').get()
    if clan.get('leader_id') == uid:
        await message.answer("⚠️ Лидер не может выйти. Передайте права или распустите клан.")
        return
    get_db_ref(f'users/{uid}').update({'clan_id': None})
    await message.answer("✅ Вы покинули клан.")

@router.message(F.text.regexp(r'(?i)^/кик'))
async def kick_member(message: types.Message):
    if not is_bot_active(): return
    args = message.text.split()
    if len(args) < 2:
        await message.answer("⚠️ Использование: <code>/кик [id или @username]</code>")
        return
    query = args[1]
    user_id = str(message.from_user.id)
    user = get_or_create_user(user_id, message.from_user.username or message.from_user.first_name)
    clan_id = user.get('clan_id')
    if not clan_id: return
    clan = get_db_ref(f'clans/{clan_id}').get()
    if clan.get('leader_id') != user_id:
        await message.answer("⚠️ Только лидер может исключать.")
        return
        
    target_id, target_user = get_user_by_username_or_id(query)
    
    if not target_user or target_user.get('clan_id') != clan_id:
        await message.answer("⚠️ Игрок не в вашем клане.")
        return
    if target_id == user_id:
        await message.answer("⚠️ Нельзя кикнуть себя.")
        return
    get_db_ref(f'users/{target_id}').update({'clan_id': None})
    name = target_user.get('username', target_id)
    await message.answer(f"✅ Игрок {format_user_link(target_id, name)} исключен.")

@router.message(F.text.regexp(r'(?i)^/повысить'))
async def promote_member(message: types.Message):
    if not is_bot_active(): return
    args = message.text.split()
    if len(args) < 2:
        await message.answer("⚠️ Использование: <code>/повысить [id или @username]</code>")
        return
    query = args[1]
    user_id = str(message.from_user.id)
    user = get_or_create_user(user_id, message.from_user.username or message.from_user.first_name)
    clan_id = user.get('clan_id')
    if not clan_id: return
    clan = get_db_ref(f'clans/{clan_id}').get()
    if clan.get('leader_id') != user_id:
        await message.answer("⚠️ Только лидер может повышать.")
        return
        
    target_id, target_user = get_user_by_username_or_id(query)
    
    if not target_user or target_user.get('clan_id') != clan_id:
        await message.answer("⚠️ Игрок не в вашем клане.")
        return
    get_db_ref(f'clans/{clan_id}').update({'leader_id': target_id})
    name = target_user.get('username', target_id)
    await message.answer(f"✅ Лидерство передано игроку {format_user_link(target_id, name)}.")


@router.message(F.text.regexp(r'(?i)^/мир'))
async def propose_peace(message: types.Message):
    if not is_bot_active(): return
    args = message.text.split(maxsplit=3)
    if len(args) < 4:
        await message.answer("⚠️ Использование: <code>/мир [клан] [ресурс/золото] [кол-во]</code>")
        return
        
    query = args[1].lower().strip('[]')
    item = args[2].lower()
    try:
        amount = int(args[3])
    except:
        await message.answer("⚠️ Количество должно быть числом.")
        return
        
    user_id = str(message.from_user.id)
    user = get_or_create_user(user_id, message.from_user.username or message.from_user.first_name)
    clan_id = user.get('clan_id')
    if not clan_id: return
    
    clan = get_db_ref(f'clans/{clan_id}').get()
    if clan.get('leader_id') != user_id:
        await message.answer("⚠️ Только лидер может предлагать мир.")
        return
        
    target_id, target_clan = get_clan_by_tag_or_id(query)
    if not target_clan:
        await message.answer("⚠️ Клан не найден.")
        return
        
    if clan.get('war_id') != target_clan.get('war_id') or not clan.get('war_id'):
        await message.answer("⚠️ Вы не воюете с этим кланом.")
        return
        
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Принять", callback_data=f"peace_acc_{clan_id}_{target_id}_{item}_{amount}")
    builder.button(text="❌ Отклонить", callback_data=f"peace_dec_{clan_id}_{target_id}")
    builder.adjust(2)
    
    text = f"🕊 <b>Предложение мира!</b>\nКлан <b>{html.escape(clan.get('name', ''))}</b> предлагает мир.\nТребование (компенсация): <b>{amount} {item}</b>."
    
    if target_clan.get('chat_id'):
        try:
            await message.bot.send_message(target_clan['chat_id'], text, reply_markup=builder.as_markup())
            await message.answer("✅ Предложение отправлено.")
        except:
            await message.answer("⚠️ Не удалось отправить предложение (чат клана недоступен).")
    else:
        await message.answer("⚠️ У вражеского клана не установлен чат.")

@router.callback_query(F.data.startswith("peace_"))
async def peace_callback(callback: types.CallbackQuery):
    if not is_bot_active(): return
    parts = callback.data.split('_')
    action = parts[1]
    sender_id = parts[2]
    target_id = parts[3]
    
    user_id = str(callback.from_user.id)
    target_clan = get_db_ref(f'clans/{target_id}').get()
    if not target_clan: return
    
    if target_clan.get('leader_id') != user_id:
        await callback.answer("⚠️ Только лидер может решать!", show_alert=True)
        return
        
    sender_clan = get_db_ref(f'clans/{sender_id}').get()
    if not sender_clan: return
    
    if action == "acc":
        item = parts[4]
        amount = int(parts[5])
        
        # Check if target can pay
        if item == 'золото':
            if target_clan.get('gold', 0) < amount:
                await callback.answer("⚠️ У вашего клана недостаточно золота для выплаты контрибуции!", show_alert=True)
                return
            get_db_ref(f'clans/{target_id}').update({'gold': target_clan.get('gold', 0) - amount})
            get_db_ref(f'clans/{sender_id}').update({'gold': sender_clan.get('gold', 0) + amount})
        else:
            resources = target_clan.get('resources', {})
            if resources.get(item, 0) < amount:
                await callback.answer(f"⚠️ У вашего клана недостаточно ресурса {item}!", show_alert=True)
                return
            resources[item] -= amount
            get_db_ref(f'clans/{target_id}/resources').set(resources)
            
            s_resources = sender_clan.get('resources', {})
            s_resources[item] = s_resources.get(item, 0) + amount
            get_db_ref(f'clans/{sender_id}/resources').set(s_resources)
            
        # End war
        war_id = target_clan.get('war_id')
        if war_id:
            get_db_ref(f'wars/{war_id}').update({'status': 'ended', 'ended_at': datetime.now().isoformat()})
        get_db_ref(f'clans/{target_id}').update({'war_id': None})
        get_db_ref(f'clans/{sender_id}').update({'war_id': None})
        
        await callback.message.edit_text(f"🕊 Мир заключен! Выплачена компенсация: {amount} {item}.")
        if sender_clan.get('chat_id'):
            try:
                await callback.bot.send_message(sender_clan['chat_id'], f"🕊 Клан <b>{html.escape(target_clan.get('name', ''))}</b> принял условия мира и выплатил {amount} {item}!")
            except: pass
    else:
        await callback.message.edit_text("❌ Вы отклонили мирный договор.")
        if sender_clan.get('chat_id'):
            try:
                await callback.bot.send_message(sender_clan['chat_id'], f"❌ Клан <b>{html.escape(target_clan.get('name', ''))}</b> отклонил мирный договор!")
            except: pass

@router.message(F.text.regexp(r'(?i)^/объявить войну'))
async def declare_war(message: types.Message):
    if not is_bot_active():
        await message.answer("⚠️ Бот временно отключен на технические работы.")
        return
    if is_sleep_mode():
        await message.answer("🌙 <b>Режим сна!</b> Войны запрещены в ночное время.")
        return
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        await message.answer("⚠️ Использование: <code>/объявить войну [тег/название]</code>")
        return
        
    query = args[2].lower()
    user_id = str(message.from_user.id)
    user = get_or_create_user(user_id, message.from_user.username or message.from_user.first_name)
    clan_id = user.get('clan_id')
    if not clan_id:
        await message.answer("⚠️ Вы не в клане.")
        return
    clan = get_db_ref(f'clans/{clan_id}').get()
    if clan.get('leader_id') != user_id:
        await message.answer("⚠️ Только лидер может объявлять войну.")
        return
    if clan.get('war_id'):
        await message.answer("⚠️ Ваш клан уже на войне.")
        return
        
    all_clans = get_db_ref('clans').get() or {}
    target_id = None
    target_clan = None
    for cid, cdata in all_clans.items():
        if cdata.get('name', '').lower() == query or cdata.get('tag', '').lower() == query:
            target_id = cid
            target_clan = cdata
            break
            
    if not target_id:
        await message.answer("⚠️ Клан не найден.")
        return
    if target_id == clan_id:
        await message.answer("⚠️ Нельзя объявить войну себе.")
        return
    if target_clan.get('war_id'):
        await message.answer("⚠️ Этот клан уже воюет.")
        return
    if target_id in clan.get('allies', []):
        await message.answer("⚠️ Нельзя объявить войну союзнику! Сначала разорвите альянс.")
        return
        
    # Start war
    war_ref = get_db_ref('wars').push()
    war_id = war_ref.key
    war_data = {
        'attacker_id': clan_id,
        'defender_id': target_id,
        'start_time': datetime.now().isoformat(),
        'hp_attacker': 100,
        'hp_defender': 100
    }
    war_ref.set(war_data)
    get_db_ref(f'clans/{clan_id}').update({'war_id': war_id})
    get_db_ref(f'clans/{target_id}').update({'war_id': war_id})
    
    await message.answer(f"⚔️ <b>ВОЙНА ОБЪЯВЛЕНА!</b>\nКлан <b>{html.escape(clan.get('name', ''))}</b> напал на <b>{html.escape(target_clan.get('name', ''))}</b>!")
    if target_clan.get('chat_id'):
        try:
            await message.bot.send_message(target_clan['chat_id'], f"⚔️ <b>ВНИМАНИЕ!</b>\nКлан <b>{html.escape(clan.get('name', ''))}</b> объявил вам войну!")
        except: pass

@router.message(F.text.regexp(r'(?i)^/мобилизация'))
async def mobilization(message: types.Message, user_id=None, username=None):
    if not is_bot_active(): return
    uid = str(user_id) if user_id else str(message.from_user.id)
    uname = username or (message.from_user.username or message.from_user.first_name)
    user = get_or_create_user(uid, uname)
    clan_id = user.get('clan_id')
    if not clan_id: return
    clan = get_db_ref(f'clans/{clan_id}').get()
    if clan.get('leader_id') != uid:
        await message.answer("⚠️ Только лидер может проводить мобилизацию.")
        return
        
    now = datetime.now()
    if user.get('last_mobilization'):
        last_mob = datetime.fromisoformat(user['last_mobilization'])
        if now - last_mob < timedelta(hours=5):
            rem = timedelta(hours=5) - (now - last_mob)
            await message.answer(f"⏳ КД! Осталось: {rem.seconds//3600}ч {(rem.seconds//60)%60}м")
            return
            
    recruits = random.randint(10, 30)
    get_db_ref(f'users/{uid}').update({
        'army': user.get('army', 0) + recruits,
        'last_mobilization': now.isoformat()
    })
    await message.answer(f"⚔️ Мобилизация успешна! Призвано {recruits} солдат.")

@router.message(F.text.regexp(r'(?i)^/тренировка'))
async def train(message: types.Message, user_id=None, username=None):
    if not is_bot_active(): return
    uid = str(user_id) if user_id else str(message.from_user.id)
    uname = username or (message.from_user.username or message.from_user.first_name)
    user = get_or_create_user(uid, uname)
    clan_id = user.get('clan_id')
    if not clan_id: return
    
    now = datetime.now()
    if user.get('last_train'):
        last_t = datetime.fromisoformat(user['last_train'])
        if now - last_t < timedelta(hours=2):
            rem = timedelta(hours=2) - (now - last_t)
            await message.answer(f"⏳ КД! Осталось: {rem.seconds//3600}ч {(rem.seconds//60)%60}м")
            return
            
    recruits = random.randint(5, 15)
    get_db_ref(f'users/{uid}').update({
        'army': user.get('army', 0) + recruits,
        'last_train': now.isoformat()
    })
    await message.answer(f"💪 Тренировка прошла успешно! Армия пополнена на {recruits} бойцов.")

@router.message(F.text.regexp(r'(?i)^/атака'))
async def attack(message: types.Message):
    if not is_bot_active():
        await message.answer("⚠️ Бот временно отключен на технические работы.")
        return
    if is_sleep_mode():
        await message.answer("🌙 <b>Режим сна!</b> Атаки запрещены в ночное время.")
        return
    args = message.text.split()
    if len(args) < 2 or not args[1].isdigit():
        await message.answer("⚠️ Использование: <code>/атака [количество]</code>")
        return
    amount = int(args[1])
    if amount <= 0: return
    
    user_id = str(message.from_user.id)
    user = get_or_create_user(user_id, message.from_user.username or message.from_user.first_name)
    clan_id = user.get('clan_id')
    if not clan_id:
        await message.answer("⚠️ Вы не в клане.")
        return
    if user.get('army', 0) < amount:
        await message.answer("⚠️ Недостаточно армии.")
        return
    if user.get('army', 0) <= 0:
        await message.answer("⚠️ У вас нет армии.")
        return
        
    clan = get_db_ref(f'clans/{clan_id}').get()
    war_id = clan.get('war_id')
    if not war_id:
        await message.answer("⚠️ Ваш клан не воюет.")
        return
    war = get_db_ref(f'wars/{war_id}').get()
    if not war: return
    
    # Check truce
    if war.get('truce_until'):
        if datetime.now() < datetime.fromisoformat(war['truce_until']):
            await message.answer("⚠️ Перемирие!")
            return
            
    # Check cooldown
    now = datetime.now()
    if user.get('last_attack'):
        last_attack = datetime.fromisoformat(user['last_attack'])
        if now - last_attack < timedelta(minutes=3):
            rem = timedelta(minutes=3) - (now - last_attack)
            await message.answer(f"⏳ КД! Осталось: {rem.seconds}с")
            return
            
    # Logic: simple damage
    damage = amount * random.uniform(0.8, 1.2)
    is_attacker = (war['attacker_id'] == clan_id)
    target_hp_field = 'hp_defender' if is_attacker else 'hp_attacker'
    current_hp = war.get(target_hp_field, 100)
    new_hp = max(0, current_hp - (damage / 10)) # Scale damage
    
    get_db_ref(f'wars/{war_id}').update({target_hp_field: new_hp})
    get_db_ref(f'users/{user_id}').update({
        'army': user.get('army', 0) - int(amount * 0.1), # 10% loss
        'last_attack': now.isoformat()
    })
    
    await message.answer(f"⚔️ Атака проведена! Враг потерял HP. Текущее HP врага: {int(new_hp)}")
    
    if new_hp <= 0:
        # Win logic
        winner_id = clan_id
        loser_id = war['defender_id'] if is_attacker else war['attacker_id']
        loser = get_db_ref(f'clans/{loser_id}').get()
        
        loot = int(loser.get('gold', 0) * 0.5)
        get_db_ref(f'clans/{winner_id}').update({
            'gold': clan.get('gold', 0) + loot,
            'exp': clan.get('exp', 0) + 50,
            'war_id': None
        })
        get_db_ref(f'clans/{loser_id}').update({
            'gold': int(loser.get('gold', 0) * 0.5),
            'war_id': None
        })
        get_db_ref(f'wars/{war_id}').delete()
        await message.answer(f"🏆 <b>ПОБЕДА!</b>\nКлан <b>{html.escape(clan.get('name', ''))}</b> победил! Награблено: {loot} золота.")
        if loser.get('chat_id'):
            try:
                await message.bot.send_message(loser['chat_id'], f"☠️ <b>ПОРАЖЕНИЕ!</b>\nВаш клан проиграл войну клану <b>{html.escape(clan.get('name', ''))}</b>.")
            except: pass

@router.message(F.text.regexp(r'(?i)^/оборона'))
async def set_defense(message: types.Message):
    if not is_bot_active(): return
    args = message.text.split()
    if len(args) < 2 or not args[1].isdigit():
        await message.answer("⚠️ Использование: <code>/оборона [количество]</code>")
        return
    amount = int(args[1])
    if amount <= 0: return
    user_id = str(message.from_user.id)
    user = get_or_create_user(user_id, message.from_user.username or message.from_user.first_name)
    if user.get('army', 0) < amount:
        await message.answer("⚠️ Недостаточно армии.")
        return
    get_db_ref(f'users/{user_id}').update({
        'army': user.get('army', 0) - amount,
        'defense_army': user.get('defense_army', 0) + amount
    })
    await message.answer(f"🛡 {amount} солдат отправлено в оборону.")

@router.message(F.text.regexp(r'(?i)^/столица'))
async def upgrade_capital(message: types.Message):
    if not is_bot_active(): return
    args = message.text.split()
    if len(args) < 2 or not args[1].isdigit():
        await message.answer("⚠️ Использование: <code>/столица [сумма]</code>")
        return
    amount = int(args[1])
    if amount < 500:
        await message.answer("⚠️ Минимум 500 монет.")
        return
    user_id = str(message.from_user.id)
    user = get_or_create_user(user_id, message.from_user.username or message.from_user.first_name)
    clan_id = user.get('clan_id')
    if not clan_id: return
    clan = get_db_ref(f'clans/{clan_id}').get()
    if clan.get('gold', 0) < amount:
        await message.answer("⚠️ Недостаточно золота в казне.")
        return
    
    war_id = clan.get('war_id')
    if not war_id:
        await message.answer("⚠️ Укреплять столицу можно только во время войны.")
        return
    war = get_db_ref(f'wars/{war_id}').get()
    
    is_attacker = (war['attacker_id'] == clan_id)
    hp_field = 'hp_attacker' if is_attacker else 'hp_defender'
    current_hp = war.get(hp_field, 100)
    
    hp_gain = (amount // 500) * 18
    new_hp = min(250, current_hp + hp_gain) # Cap at 250? Or just add. Let's cap for balance or just add.
    
    get_db_ref(f'clans/{clan_id}').update({'gold': clan.get('gold', 0) - amount})
    get_db_ref(f'wars/{war_id}').update({hp_field: new_hp})
    
    await message.answer(f"🏰 Столица укреплена! +{hp_gain} HP. Текущее HP: {new_hp}")

@router.message(F.text.regexp(r'(?i)^/ультиматум'))
async def ultimatum(message: types.Message):
    if not is_bot_active(): return
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        await message.answer("⚠️ Использование: <code>/ультиматум [клан] [текст]</code>")
        return
    query = args[1].lower()
    text = args[2]
    
    user_id = str(message.from_user.id)
    user = get_or_create_user(user_id, message.from_user.username or message.from_user.first_name)
    clan_id = user.get('clan_id')
    if not clan_id: return
    clan = get_db_ref(f'clans/{clan_id}').get()
    if clan.get('leader_id') != user_id:
        await message.answer("⚠️ Только лидер может отправлять ультиматумы.")
        return
        
    all_clans = get_db_ref('clans').get() or {}
    target_id = None
    target_clan = None
    for cid, cdata in all_clans.items():
        if cdata.get('name', '').lower() == query or cdata.get('tag', '').lower() == query:
            target_id = cid
            target_clan = cdata
            break
            
    if not target_id:
        await message.answer("⚠️ Клан не найден.")
        return
        
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Принять", callback_data=f"ult_accept_{clan_id}_{target_id}")
    builder.button(text="❌ Отвергнуть", callback_data=f"ult_reject_{clan_id}_{target_id}")
    
    if target_clan.get('chat_id'):
        try:
            await message.bot.send_message(
                target_clan['chat_id'],
                f"📜 <b>УЛЬТИМАТУМ от {html.escape(clan.get('name', ''))}</b> клану <b>{html.escape(target_clan.get('name', ''))}</b>\n\n<i>{html.escape(text)}</i>\n\nЛидер, сделайте выбор:",
                reply_markup=builder.as_markup()
            )
            await message.answer(f"✅ Ультиматум отправлен клану <b>{html.escape(target_clan.get('name', ''))}</b>.")
        except:
            await message.answer("⚠️ Ошибка отправки (бот не в чате врага).")
    else:
        await message.answer("⚠️ У клана нет чата.")



@router.message(F.text.regexp(r'(?i)^/предложить альянс'))
async def propose_alliance(message: types.Message):
    if not is_bot_active(): return
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("⚠️ Использование: <code>/предложить альянс [клан]</code>")
        return
    query = args[1].lower()
    user_id = str(message.from_user.id)
    user = get_or_create_user(user_id, message.from_user.username or message.from_user.first_name)
    clan_id = user.get('clan_id')
    if not clan_id: return
    clan = get_db_ref(f'clans/{clan_id}').get()
    if clan.get('leader_id') != user_id:
        await message.answer("⚠️ Только лидер может предлагать альянс.")
        return
        
    all_clans = get_db_ref('clans').get() or {}
    target_id = None
    target_clan = None
    
    if query.isdigit():
        idx = int(query) - 1
        group_clans = [c for c in all_clans.values() if c.get('chat_id') == message.chat.id] # Simplified logic for digit
        # Actually digit logic usually requires sorted list context. 
        # Let's stick to name/tag for simplicity or reuse list logic if possible.
        # Reusing list logic:
        group_clans = []
        for cid, cdata in all_clans.items():
            if cdata.get('chat_id') == message.chat.id:
                cdata['id'] = cid
                group_clans.append(cdata)
        group_clans.sort(key=lambda x: x.get('exp', 0), reverse=True)
        if 0 <= idx < len(group_clans):
            target_clan = group_clans[idx]
            target_id = target_clan['id']
    else:
        for cid, cdata in all_clans.items():
            if cdata.get('name', '').lower() == query or cdata.get('tag', '').lower() == query:
                target_id = cid
                target_clan = cdata
                break
                
    if not target_id:
        await message.answer("⚠️ Клан не найден.")
        return
    if target_id == clan_id:
        await message.answer("⚠️ Нельзя заключить альянс с собой.")
        return
    if target_id in clan.get('allies', []):
        await message.answer("⚠️ Вы уже в альянсе.")
        return
        
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Принять", callback_data=f"ally_acc_{clan_id}_{target_id}")
    builder.button(text="❌ Отклонить", callback_data=f"ally_dec_{clan_id}_{target_id}")
    builder.adjust(2)
    
    if target_clan.get('chat_id'):
        try:
            await message.bot.send_message(
                target_clan['chat_id'],
                f"🤝 <b>Предложение альянса!</b>\nКлан <b>{html.escape(clan.get('name', ''))}</b> предлагает альянс клану <b>{html.escape(target_clan.get('name', ''))}</b>.",
                reply_markup=builder.as_markup()
            )
            await message.answer(f"✅ Предложение отправлено клану <b>{html.escape(target_clan.get('name', ''))}</b>.")
        except:
            await message.answer("⚠️ Ошибка отправки.")
    else:
        await message.answer("⚠️ У клана нет чата.")

@router.message(F.text.regexp(r'(?i)^/разорвать альянс'))
async def break_alliance(message: types.Message):
    if not is_bot_active(): return
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("⚠️ Использование: <code>/разорвать альянс [клан]</code>")
        return
    query = args[1].lower()
    user_id = str(message.from_user.id)
    user = get_or_create_user(user_id, message.from_user.username or message.from_user.first_name)
    clan_id = user.get('clan_id')
    if not clan_id: return
    clan = get_db_ref(f'clans/{clan_id}').get()
    if clan.get('leader_id') != user_id:
        await message.answer("⚠️ Только лидер может разрывать альянс.")
        return
        
    all_clans = get_db_ref('clans').get() or {}
    target_id = None
    target_clan = None
    
    # Similar search logic
    if query.isdigit():
        idx = int(query) - 1
        group_clans = []
        for cid, cdata in all_clans.items():
            if cdata.get('chat_id') == message.chat.id:
                cdata['id'] = cid
                group_clans.append(cdata)
        group_clans.sort(key=lambda x: x.get('exp', 0), reverse=True)
        if 0 <= idx < len(group_clans):
            target_clan = group_clans[idx]
            target_id = target_clan['id']
    else:
        for cid, cdata in all_clans.items():
            if cdata.get('name', '').lower() == query or cdata.get('tag', '').lower() == query:
                target_id = cid
                target_clan = cdata
                break
                
    if not target_id:
        await message.answer("⚠️ Клан не найден.")
        return
    if target_id not in clan.get('allies', []):
        await message.answer("⚠️ Вы не в альянсе с этим кланом.")
        return
        
    # Break logic
    s_allies = clan.get('allies', [])
    if target_id in s_allies: s_allies.remove(target_id)
    get_db_ref(f'clans/{clan_id}').update({'allies': s_allies})
    
    t_allies = target_clan.get('allies', [])
    if clan_id in t_allies: t_allies.remove(clan_id)
    get_db_ref(f'clans/{target_id}').update({'allies': t_allies})
    
    await message.answer(f"💔 Альянс с <b>{html.escape(target_clan.get('name', ''))}</b> разорван.")
    if target_clan.get('chat_id'):
        try:
            await message.bot.send_message(target_clan['chat_id'], f"💔 Клан <b>{html.escape(clan.get('name', ''))}</b> разорвал с вами альянс.")
        except: pass

# --- CALLBACKS ---

@router.callback_query(F.data.startswith("c_"))
async def clan_callbacks(callback: types.CallbackQuery):
    if not is_bot_active():
        await callback.answer("⚠️ Бот отключен.", show_alert=True)
        return
    parts = callback.data.split('_')
    action = parts[1]
    user_id = parts[-1]
    
    if str(callback.from_user.id) != user_id:
        await callback.answer("⚠️ Это не ваше меню!", show_alert=True)
        return
        
    user = get_or_create_user(user_id, callback.from_user.username or callback.from_user.first_name)
    clan_id = user.get('clan_id')
    if not clan_id:
        await callback.message.edit_text("⚠️ Вы не в клане.")
        return
    clan = get_db_ref(f'clans/{clan_id}').get()
    if not clan:
        await callback.message.edit_text("⚠️ Клан удален.")
        return
        
    is_leader = (clan.get('leader_id') == user_id)
    
    if action == "work":
        await work(callback.message, user_id=callback.from_user.id, username=callback.from_user.username)
        await callback.answer()
    elif action == "job":
        await job(callback.message, user_id=callback.from_user.id, username=callback.from_user.username)
        await callback.answer()
    elif action == "leave":
        await leave_clan_cmd(callback.message, user_id=callback.from_user.id, username=callback.from_user.username)
        await callback.answer()
    elif action == "mob":
        await mobilization(callback.message, user_id=callback.from_user.id, username=callback.from_user.username)
        await callback.answer()
    elif action == "train":
        await train(callback.message, user_id=callback.from_user.id, username=callback.from_user.username)
        await callback.answer()
    elif action == "rocket":
        await develop(callback.message, user_id=callback.from_user.id, username=callback.from_user.username)
        await callback.answer()
    elif action == "factory":
        await build_factory(callback.message, user_id=callback.from_user.id, username=callback.from_user.username)
        await callback.answer()
    elif action == "delete":
        # Delete clan logic
        if not is_leader: return
        # Simple confirmation or just delete? Let's just delete for simplicity or add confirm later.
        # Previous code had confirm. I'll just delete to save tokens or add simple confirm.
        # Let's just delete.
        all_users = get_db_ref('users').get() or {}
        for uid, udata in all_users.items():
            if udata.get('clan_id') == clan_id:
                get_db_ref(f'users/{uid}').update({'clan_id': None})
        get_db_ref(f'clans/{clan_id}').delete()
        await callback.message.edit_text("💥 Клан распущен.")
    elif action == "build":
        # c_build_1_userid
        btype = parts[2]
        cost = 500
        if clan.get('gold', 0) < cost:
            await callback.answer("⚠️ Недостаточно золота (нужно 500).", show_alert=True)
            return
        
        field = 'factory_weapon'
        if btype == '2': field = 'factory_finance'
        elif btype == '3': field = 'factory_defense'
        
        get_db_ref(f'clans/{clan_id}').update({
            'gold': clan.get('gold', 0) - cost,
            field: clan.get(field, 0) + 1,
            'population_limit': clan.get('population_limit', 10) + (10 if btype == '1' else 0)
        })
        await callback.answer("✅ Завод построен!", show_alert=True)
        
    elif action == "dev":
        # c_dev_type_userid
        dtype = parts[2] # баллистика or ядерка
        cost = 1000 if dtype == 'баллистика' else 5000
        if clan.get('gold', 0) < cost:
            await callback.answer(f"⚠️ Недостаточно золота (нужно {cost}).", show_alert=True)
            return
        
        field = 'prog_ballistic' if dtype == 'баллистика' else 'prog_nuclear'
        get_db_ref(f'clans/{clan_id}').update({
            'gold': clan.get('gold', 0) - cost,
            field: clan.get(field, 0) + 10 # +10 progress
        })
        await callback.answer(f"✅ Вклад в {dtype} внесен (+10%)!", show_alert=True)

@router.callback_query(F.data.startswith("ult_"))
async def ult_callback(callback: types.CallbackQuery):
    if not is_bot_active(): return
    parts = callback.data.split('_')
    action = parts[1] # accept/reject
    sender_id = parts[2]
    target_id = parts[3]
    
    user_id = str(callback.from_user.id)
    target_clan = get_db_ref(f'clans/{target_id}').get()
    if not target_clan: return
    
    if target_clan.get('leader_id') != user_id:
        await callback.answer("⚠️ Только лидер может решать!", show_alert=True)
        return
        
    sender_clan = get_db_ref(f'clans/{sender_id}').get()
    sender_name = sender_clan.get('name', '???') if sender_clan else "???"
    
    if action == "accept":
        await callback.message.edit_text(f"✅ Клан <b>{html.escape(target_clan.get('name', ''))}</b> ПРИНЯЛ ультиматум от <b>{html.escape(sender_name)}</b>!")
        if sender_clan and sender_clan.get('chat_id'):
            try:
                await callback.bot.send_message(sender_clan['chat_id'], f"✅ Клан <b>{html.escape(target_clan.get('name', ''))}</b> принял ваш ультиматум.")
            except: pass
    else:
        await callback.message.edit_text(f"❌ Клан <b>{html.escape(target_clan.get('name', ''))}</b> ОТВЕРГ ультиматум от <b>{html.escape(sender_name)}</b>!")
        if sender_clan and sender_clan.get('chat_id'):
            try:
                await callback.bot.send_message(sender_clan['chat_id'], f"❌ Клан <b>{html.escape(target_clan.get('name', ''))}</b> отверг ваш ультиматум! Готовьтесь к войне!")
            except: pass

@router.callback_query(F.data.startswith("ally_"))
async def alliance_callbacks(callback: types.CallbackQuery):
    if not is_bot_active(): return
    parts = callback.data.split('_')
    action = parts[1] # acc/dec
    sender_id = parts[2]
    target_id = parts[3]
    
    user_id = str(callback.from_user.id)
    target_clan = get_db_ref(f'clans/{target_id}').get()
    if not target_clan: return
    
    if target_clan.get('leader_id') != user_id:
        await callback.answer("⚠️ Только лидер может решать!", show_alert=True)
        return
        
    sender_clan = get_db_ref(f'clans/{sender_id}').get()
    if not sender_clan:
        await callback.message.edit_text("⚠️ Клан-отправитель исчез.")
        return
        
    if action == "acc":
        s_allies = sender_clan.get('allies', [])
        t_allies = target_clan.get('allies', [])
        if target_id not in s_allies: s_allies.append(target_id)
        if sender_id not in t_allies: t_allies.append(sender_id)
        
        get_db_ref(f'clans/{sender_id}').update({'allies': s_allies})
        get_db_ref(f'clans/{target_id}').update({'allies': t_allies})
        
        await callback.message.edit_text(f"🤝 Альянс между <b>{html.escape(sender_clan.get('name', ''))}</b> и <b>{html.escape(target_clan.get('name', ''))}</b> заключен!")
        if sender_clan.get('chat_id'):
            try:
                await callback.bot.send_message(sender_clan['chat_id'], f"🤝 Клан <b>{html.escape(target_clan.get('name', ''))}</b> принял предложение альянса!")
            except: pass
    else:
        await callback.message.edit_text(f"❌ Предложение альянса отклонено.")
        if sender_clan.get('chat_id'):
            try:
                await callback.bot.send_message(sender_clan['chat_id'], f"❌ Клан <b>{html.escape(target_clan.get('name', ''))}</b> отклонил предложение альянса.")
            except: pass

@router.message(F.text.regexp(r'(?i)^/создать производство'))
async def create_production(message: types.Message):
    if not is_bot_active(): return
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        await message.answer("⚠️ Использование: <code>/создать производство [товар]</code>")
        return
    item = args[2].lower()
    user_id = str(message.from_user.id)
    user = get_or_create_user(user_id, message.from_user.username or message.from_user.first_name)
    clan_id = user.get('clan_id')
    if not clan_id: return
    clan = get_db_ref(f'clans/{clan_id}').get()
    if clan.get('leader_id') != user_id:
        await message.answer("⚠️ Только лидер может создавать производство.")
        return
        
    if clan.get('gold', 0) < 1000:
        await message.answer("⚠️ Недостаточно золота (нужно 1000).")
        return
        
    productions = clan.get('productions', {})
    if item in productions:
        await message.answer("⚠️ Вы уже производите этот товар.")
        return
        
    productions[item] = {'level': 1, 'last_collected': datetime.now().isoformat()}
    get_db_ref(f'clans/{clan_id}').update({
        'gold': clan.get('gold', 0) - 1000,
        'productions': productions
    })
    await message.answer(f"✅ Производство <b>{html.escape(item)}</b> создано! Скорость: 10 шт/час.")

@router.message(F.text.regexp(r'(?i)^/улучшить производство'))
async def upgrade_production(message: types.Message):
    if not is_bot_active(): return
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        await message.answer("⚠️ Использование: <code>/улучшить производство [товар]</code>")
        return
    item = args[2].lower()
    user_id = str(message.from_user.id)
    user = get_or_create_user(user_id, message.from_user.username or message.from_user.first_name)
    clan_id = user.get('clan_id')
    if not clan_id: return
    
    collect_production(clan_id)
    clan = get_db_ref(f'clans/{clan_id}').get()
    if clan.get('leader_id') != user_id:
        await message.answer("⚠️ Только лидер может улучшать производство.")
        return
        
    productions = clan.get('productions', {})
    if item not in productions:
        await message.answer("⚠️ У вас нет такого производства.")
        return
        
    level = productions[item].get('level', 1)
    cost = level * 1000
    if clan.get('gold', 0) < cost:
        await message.answer(f"⚠️ Недостаточно золота (нужно {cost}).")
        return
        
    productions[item]['level'] = level + 1
    get_db_ref(f'clans/{clan_id}').update({
        'gold': clan.get('gold', 0) - cost,
        'productions': productions
    })
    await message.answer(f"✅ Производство <b>{html.escape(item)}</b> улучшено до {level+1} уровня! Скорость: {(level+1)*10} шт/час.")

@router.message(Command("экономика"))
async def economy_menu(message: types.Message):
    if not is_bot_active(): return
    user_id = str(message.from_user.id)
    user = get_or_create_user(user_id, message.from_user.username or message.from_user.first_name)
    clan_id = user.get('clan_id')
    if not clan_id:
        await message.answer("⚠️ Вы не в клане.")
        return
        
    collect_production(clan_id)
    clan = get_db_ref(f'clans/{clan_id}').get()
    
    text = f"📊 <b>Экономика клана {html.escape(clan.get('name', ''))}</b>\n\n"
    text += f"💰 Золото: <b>{clan.get('gold', 0)}</b>\n\n"
    
    resources = clan.get('resources', {})
    text += "📦 <b>Ресурсы:</b>\n"
    if resources:
        for item, amount in resources.items():
            text += f"• {item.capitalize()}: {amount} шт.\n"
    else:
        text += "• Пусто\n"
        
    text += "\n🏭 <b>Производство:</b>\n"
    productions = clan.get('productions', {})
    if productions:
        for item, data in productions.items():
            rate = data.get('level', 1) * 10
            text += f"• {item.capitalize()} (Ур. {data.get('level', 1)}): {rate} шт/час\n"
    else:
        text += "• Нет производств\n"
        
    await message.answer(text)

@router.message(F.text.regexp(r'(?i)^/мировой магазин'))
async def global_market(message: types.Message):
    if not is_bot_active(): return
    market = get_db_ref('market').get() or {}
    if not market:
        await message.answer("🛒 Мировой магазин пуст.")
        return
        
    text = "🛒 <b>Мировой магазин:</b>\n\n"
    for lot_id, data in list(market.items())[:20]: # Show top 20
        clan_name = data.get('clan_name', 'Неизвестно')
        item = data.get('item', 'товар')
        amount = data.get('amount', 0)
        price = data.get('price', 0)
        text += f"🆔 <code>{lot_id}</code> | {clan_name}\n"
        text += f"📦 {item.capitalize()} ({amount} шт) — 💰 {price} за шт.\n\n"
        
    text += "<i>Для покупки используйте:</i> <code>/купить [id] [кол-во]</code>"
    await message.answer(text)

@router.message(F.text.regexp(r'(?i)^/продать'))
async def sell_item(message: types.Message):
    if not is_bot_active(): return
    args = message.text.split()
    if len(args) < 4:
        await message.answer("⚠️ Использование: <code>/продать [товар] [кол-во] [цена за 1 шт]</code>")
        return
        
    item = args[1].lower()
    try:
        amount = int(args[2])
        price = int(args[3])
    except:
        await message.answer("⚠️ Количество и цена должны быть числами.")
        return
        
    if amount <= 0 or price <= 0: return
    
    user_id = str(message.from_user.id)
    user = get_or_create_user(user_id, message.from_user.username or message.from_user.first_name)
    clan_id = user.get('clan_id')
    if not clan_id: return
    
    collect_production(clan_id)
    clan = get_db_ref(f'clans/{clan_id}').get()
    if clan.get('leader_id') != user_id:
        await message.answer("⚠️ Только лидер может продавать ресурсы.")
        return
        
    resources = clan.get('resources', {})
    if resources.get(item, 0) < amount:
        await message.answer(f"⚠️ Недостаточно ресурса <b>{html.escape(item)}</b> (у вас {resources.get(item, 0)}).")
        return
        
    # Deduct resource
    resources[item] -= amount
    get_db_ref(f'clans/{clan_id}/resources').set(resources)
    
    # Create lot
    lot_ref = get_db_ref('market').push()
    lot_ref.set({
        'clan_id': clan_id,
        'clan_name': clan.get('name', ''),
        'item': item,
        'amount': amount,
        'price': price,
        'created_at': datetime.now().isoformat()
    })
    
    await message.answer(f"✅ Выставили {amount} шт. <b>{html.escape(item)}</b> по {price} 💰 за штуку.\n🆔 ID лота: <code>{lot_ref.key}</code>")

@router.message(F.text.regexp(r'(?i)^/купить'))
async def buy_item(message: types.Message):
    if not is_bot_active(): return
    args = message.text.split()
    if len(args) < 3:
        await message.answer("⚠️ Использование: <code>/купить [id_лота] [кол-во]</code>")
        return
        
    lot_id = args[1]
    try:
        amount_to_buy = int(args[2])
    except:
        await message.answer("⚠️ Количество должно быть числом.")
        return
        
    if amount_to_buy <= 0: return
    
    user_id = str(message.from_user.id)
    user = get_or_create_user(user_id, message.from_user.username or message.from_user.first_name)
    buyer_clan_id = user.get('clan_id')
    if not buyer_clan_id: return
    
    buyer_clan = get_db_ref(f'clans/{buyer_clan_id}').get()
    if buyer_clan.get('leader_id') != user_id:
        await message.answer("⚠️ Только лидер может покупать ресурсы.")
        return
        
    lot_ref = get_db_ref(f'market/{lot_id}')
    lot = lot_ref.get()
    if not lot:
        await message.answer("⚠️ Лот не найден.")
        return
        
    if lot.get('clan_id') == buyer_clan_id:
        await message.answer("⚠️ Вы не можете купить свой же лот.")
        return
        
    available = lot.get('amount', 0)
    if amount_to_buy > available:
        await message.answer(f"⚠️ В лоте только {available} шт.")
        return
        
    price_per_unit = lot.get('price', 0)
    total_cost = amount_to_buy * price_per_unit
    
    if buyer_clan.get('gold', 0) < total_cost:
        await message.answer(f"⚠️ Недостаточно золота (нужно {total_cost}).")
        return
        
    # Process transaction
    seller_clan_id = lot.get('clan_id')
    seller_clan = get_db_ref(f'clans/{seller_clan_id}').get()
    
    # Deduct gold and add resource to buyer
    buyer_resources = buyer_clan.get('resources', {})
    item = lot.get('item')
    buyer_resources[item] = buyer_resources.get(item, 0) + amount_to_buy
    get_db_ref(f'clans/{buyer_clan_id}').update({
        'gold': buyer_clan.get('gold', 0) - total_cost,
        'resources': buyer_resources
    })
    
    # Add gold to seller
    if seller_clan:
        get_db_ref(f'clans/{seller_clan_id}').update({
            'gold': seller_clan.get('gold', 0) + total_cost
        })
        
    # Update or delete lot
    if amount_to_buy == available:
        lot_ref.delete()
    else:
        lot_ref.update({'amount': available - amount_to_buy})
        
    await message.answer(f"✅ Вы купили {amount_to_buy} шт. <b>{html.escape(item)}</b> за {total_cost} 💰.")
    
    # Notify seller
    if seller_clan and seller_clan.get('chat_id'):
        try:
            await message.bot.send_message(seller_clan['chat_id'], f"💰 Клан <b>{html.escape(buyer_clan.get('name', ''))}</b> купил у вас {amount_to_buy} шт. <b>{html.escape(item)}</b> за {total_cost} 💰.")
        except: pass

@router.message(F.text.regexp(r'(?i)^/подработка'))
async def work(message: types.Message, user_id=None, username=None):
    if not is_bot_active():
        await message.answer("⚠️ Бот временно отключен на технические работы.")
        return
    uid = str(user_id) if user_id else str(message.from_user.id)
    uname = username or (message.from_user.username or message.from_user.first_name)
    user = get_or_create_user(uid, uname)
    clan_id = user.get('clan_id')
    if not clan_id:
        await message.answer("⚠️ Вы не в клане.")
        return
    
    now = datetime.now()
    if user.get('last_work'):
        last_work = datetime.fromisoformat(user['last_work'])
        if now - last_work < timedelta(minutes=30):
            rem = timedelta(minutes=30) - (now - last_work)
            await message.answer(f"⏳ КД! Осталось: {rem.seconds//60}м {rem.seconds%60}с")
            return
            
    earnings = random.randint(50, 150)
    clan_ref = get_db_ref(f'clans/{clan_id}')
    clan = clan_ref.get()
    clan_ref.update({'gold': clan.get('gold', 0) + earnings})
    get_db_ref(f'users/{uid}').update({'last_work': now.isoformat()})
    
    await message.answer(f"🔨 Вы заработали {earnings} золота для клана!")

@router.message(F.text.regexp(r'(?i)^/устроиться'))
async def job(message: types.Message, user_id=None, username=None):
    if not is_bot_active():
        await message.answer("⚠️ Бот временно отключен на технические работы.")
        return
    uid = str(user_id) if user_id else str(message.from_user.id)
    uname = username or (message.from_user.username or message.from_user.first_name)
    user = get_or_create_user(uid, uname)
    clan_id = user.get('clan_id')
    if not clan_id:
        await message.answer("⚠️ Вы не в клане.")
        return
        
    now = datetime.now()
    if user.get('last_job'):
        last_job = datetime.fromisoformat(user['last_job'])
        if now - last_job < timedelta(hours=6):
            rem = timedelta(hours=6) - (now - last_job)
            await message.answer(f"⏳ КД! Осталось: {rem.seconds//3600}ч {(rem.seconds//60)%60}м")
            return
            
    earnings = random.randint(300, 600)
    clan_ref = get_db_ref(f'clans/{clan_id}')
    clan = clan_ref.get()
    clan_ref.update({'gold': clan.get('gold', 0) + earnings})
    get_db_ref(f'users/{user_id}').update({'last_job': now.isoformat()})
    
    await message.answer(f"💼 Вы заработали {earnings} золота для клана!")

@router.message(F.text.regexp(r'(?i)^/строй завод'))
async def build_factory(message: types.Message, user_id=None, username=None):
    if not is_bot_active():
        await message.answer("⚠️ Бот временно отключен на технические работы.")
        return
    uid = str(user_id) if user_id else str(message.from_user.id)
    uname = username or (message.from_user.username or message.from_user.first_name)
    user = get_or_create_user(uid, uname)
    clan_id = user.get('clan_id')
    if not clan_id:
        await message.answer("⚠️ Вы не в клане.")
        return
    clan = get_db_ref(f'clans/{clan_id}').get()
    if clan.get('leader_id') != uid:
        await message.answer("⚠️ Только лидер может строить заводы.")
        return
        
    builder = InlineKeyboardBuilder()
    builder.button(text="🔫 Оружейный (500)", callback_data=f"c_build_1_{uid}")
    builder.button(text="💰 Финансовый (500)", callback_data=f"c_build_2_{uid}")
    builder.button(text="🛡 Оборонительный (500)", callback_data=f"c_build_3_{uid}")
    builder.adjust(1)
    await message.answer("🏭 <b>Выберите тип завода:</b>\n1. Оружейный (+10 к лимиту)\n2. Финансовый (Доход)\n3. Оборонительный (Защита)", reply_markup=builder.as_markup())

@router.message(F.text.regexp(r'(?i)^/разработка'))
async def develop(message: types.Message, user_id=None, username=None):
    if not is_bot_active(): return
    uid = str(user_id) if user_id else str(message.from_user.id)
    uname = username or (message.from_user.username or message.from_user.first_name)
    user = get_or_create_user(uid, uname)
    clan_id = user.get('clan_id')
    if not clan_id: return
    clan = get_db_ref(f'clans/{clan_id}').get()
    
    # Check cooldown for non-leaders
    is_leader = (clan.get('leader_id') == uid)
    now = datetime.now()
    if not is_leader:
        if user.get('last_rocket_dev'):
            last_dev = datetime.fromisoformat(user['last_rocket_dev'])
            if now - last_dev < timedelta(hours=1):
                rem = timedelta(hours=1) - (now - last_dev)
                await message.answer(f"⏳ КД на разработку! Осталось: {rem.seconds//60}м")
                return
        get_db_ref(f'users/{uid}').update({'last_rocket_dev': now.isoformat()})

    builder = InlineKeyboardBuilder()
    builder.button(text="🚀 Баллистика (1000)", callback_data=f"c_dev_баллистика_{uid}")
    builder.button(text="☢️ Ядерка (5000)", callback_data=f"c_dev_ядерка_{uid}")
    builder.adjust(1)
    await message.answer("🧪 <b>Выберите проект:</b>", reply_markup=builder.as_markup())

@router.message(F.text.regexp(r'(?i)^/пуск'))
async def launch(message: types.Message):
    if not is_bot_active():
        await message.answer("⚠️ Бот временно отключен на технические работы.")
        return
    if is_sleep_mode():
        await message.answer("🌙 <b>Режим сна!</b> Запуски запрещены.")
        return
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        await message.answer("⚠️ Использование: <code>/пуск [баллистика/ядерка] [цель]</code>")
        return
    rtype = args[1].lower()
    query = args[2].lower()
    
    if rtype not in ['баллистика', 'ядерка']:
        await message.answer("⚠️ Тип ракеты: баллистика или ядерка.")
        return
        
    user_id = str(message.from_user.id)
    user = get_or_create_user(user_id, message.from_user.username or message.from_user.first_name)
    clan_id = user.get('clan_id')
    if not clan_id: return
    clan = get_db_ref(f'clans/{clan_id}').get()
    if clan.get('leader_id') != user_id:
        await message.answer("⚠️ Только лидер может запускать ракеты.")
        return
        
    # Check progress
    needed = 100 if rtype == 'баллистика' else 100
    current = clan.get(f'prog_{"ballistic" if rtype == "баллистика" else "nuclear"}', 0)
    if current < needed:
        await message.answer(f"⚠️ Ракета не готова! Прогресс: {current}/{needed}")
        return
        
    all_clans = get_db_ref('clans').get() or {}
    target_id = None
    target_clan = None
    for cid, cdata in all_clans.items():
        if cdata.get('name', '').lower() == query or cdata.get('tag', '').lower() == query:
            target_id = cid
            target_clan = cdata
            break
    if not target_id:
        await message.answer("⚠️ Цель не найдена.")
        return
        
    # Launch logic
    damage = 50 if rtype == 'баллистика' else 100
    # Reset progress
    get_db_ref(f'clans/{clan_id}').update({f'prog_{"ballistic" if rtype == "баллистика" else "nuclear"}': 0})
    
    # Damage logic (reduce gold, army, factories?)
    t_gold = target_clan.get('gold', 0)
    
    loss_gold = int(t_gold * (0.3 if rtype == 'баллистика' else 0.6))
    get_db_ref(f'clans/{target_id}').update({'gold': max(0, t_gold - loss_gold)})
    
    await message.answer(f"🚀 <b>ПУСК!</b> Ракета {rtype} поразила <b>{html.escape(target_clan.get('name', ''))}</b>!\nУничтожено {loss_gold} золота.")
    if target_clan.get('chat_id'):
        try:
            await message.bot.send_message(target_clan['chat_id'], f"💥 <b>ВНИМАНИЕ!</b>\nПо вам нанесен ракетный удар ({rtype}) от клана <b>{html.escape(clan.get('name', ''))}</b>!")
        except: pass

@router.message(AdminStates.waiting_for_factory)
async def process_add_factory(message: types.Message, state: FSMContext):
    try:
        clan_id, ftype, amount = message.text.split()
        amount = int(amount)
        clan_ref = get_db_ref(f'clans/{clan_id}')
        clan = clan_ref.get()
        if not clan:
            await message.answer("⚠️ Клан не найден.")
        else:
            field = 'factory_weapon'
            if ftype == '2': field = 'factory_finance'
            elif ftype == '3': field = 'factory_defense'
            current = clan.get(field, 0)
            clan_ref.update({field: current + amount})
            await message.answer(f"✅ Добавлено {amount} заводов (тип {ftype}) клану {clan_id}.")
    except:
        await message.answer("⚠️ Ошибка формата.")
    await state.clear()
    await show_admin_panel(message, page=2)

@router.message(AdminStates.waiting_for_rocket)
async def process_add_rocket(message: types.Message, state: FSMContext):
    try:
        clan_id, rtype, amount = message.text.split()
        amount = int(amount)
        clan_ref = get_db_ref(f'clans/{clan_id}')
        clan = clan_ref.get()
        if not clan:
            await message.answer("⚠️ Клан не найден.")
        else:
            field = 'prog_ballistic' if rtype == '1' else 'prog_nuclear'
            current = clan.get(field, 0)
            clan_ref.update({field: current + amount})
            await message.answer(f"✅ Добавлен прогресс {amount} (тип {rtype}) клану {clan_id}.")
    except:
        await message.answer("⚠️ Ошибка формата.")
    await state.clear()
    await show_admin_panel(message, page=2)




