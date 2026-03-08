import logging
import html
import re
import asyncio
import random
from datetime import datetime, timedelta
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from firebase_db import get_db_ref

router = Router()

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

@router.message(Command("инфошарик"))
async def cmd_infosharyk(message: types.Message):
    text = (
        "📖 <b>Полный список команд (Скрытый справочник):</b>\n\n"
        "<b>🏰 Управление:</b>\n"
        "• <code>/создать клан [название] [тег]</code> — Создать клан\n"
        "• <code>/вступить [название или тег или номер]</code> — Вступить в клан\n"
        "• <code>/выйти</code> — Выйти из клана\n"
        "• <code>/удалить клан подтверждаю</code> — Удалить клан (лидер)\n"
        "• <code>/мой клан</code> — Статистика и инлайн-меню\n"
        "• <code>/список кланов</code> — Кланы в текущей группе\n\n"
        "<b>⚔️ Война и Дипломатия:</b>\n"
        "• <code>/предложить альянс [цель]</code> — Предложить союз\n"
        "• <code>/разорвать альянс [цель]</code> — Расторгнуть союз\n"
        "• <code>/объявить войну [цель]</code> — Начать войну\n"
        "• <code>/атака [кол-во]</code> — Ручная атака (КД 3 мин)\n"
        "• <code>/белый мир</code> — Предложить мир\n"
        "• <code>/перемирие [время]</code> — Пауза в войне (1ч, 1д)\n"
        "• <code>/капитуляция</code> — Сдаться (при 0 HP)\n"
        "• <code>/аннексия</code> — Захват территории (при &lt;20% HP врага)\n"
        "• <code>/ультиматум [цель] [текст]</code> — Отправить требование с кнопками\n\n"
        "<b>🚀 Ракеты:</b>\n"
        "• <code>/разработка [баллистика/ядерка]</code> — Вложить 10% золота (КД 1ч для граждан)\n"
        "• <code>/пуск [баллистика/ядерка] [цель]</code> — Удар по столице\n\n"
        "<b>🏭 Экономика:</b>\n"
        "• <code>/мобилизация</code> — Нанять 50-500 солдат (КД 5ч, только лидер)\n"
        "• <code>/подработка</code> — Солдаты и золото (КД 30 мин)\n"
        "• <code>/устроится</code> — 150-300 золота в казну (КД 6ч, не лидер)\n"
        "• <code>/оборона [кол-во]</code> — Перевести солдат в оборону\n"
        "• <code>/тренировка [сила/защита/здоровье]</code> — Прокачка (КД 24ч)\n"
        "• <code>/строй завод [тип]</code> — Постройка завода (КД 10 мин, только лидер)\n"
        "• <code>/столица [монеты]</code> — Укрепить столицу (500м = 18 HP, 10 мин)\n"
    )
    await message.answer(text)

@router.message(Command("boevik"))
async def cmd_boevik(message: types.Message):
    text = (
        "⚔️ <b>Справочник Клан-Бота</b> ⚔️\n\n"
        "<b>🏰 Управление кланом:</b>\n"
        "• <code>/создать клан [название] [тег]</code> — Создать новый клан\n"
        "• <code>/вступить [название или тег или номер]</code> — Присоединиться к клану\n"
        "• <code>/выйти</code> — Покинуть текущий клан\n"
        "• <code>/удалить клан подтверждаю</code> — Удалить свой клан (только лидер)\n"
        "• <code>/мой клан</code> — Показать статистику вашего клана\n"
        "• <code>/список кланов</code> — Показать кланы в этой группе\n\n"
        "<b>⚔️ Война и Дипломатия:</b>\n"
        "• <code>/предложить альянс [цель]</code> — Предложить союз с другим кланом\n"
        "• <code>/разорвать альянс [цель]</code> — Расторгнуть союз\n"
        "• <code>/объявить войну [цель]</code> — Начать войну с другим кланом (только лидер)\n"
        "• <code>/атака [кол-во]</code> — Отправить армию в атаку. КД: 3 мин\n"
        "• <code>/белый мир</code> — Предложить или принять белый мир (без потерь, только лидер)\n"
        "• <code>/перемирие [время]</code> — Предложить перемирие (например: 1ч, 1д)\n"
        "• <code>/капитуляция</code> — Признать поражение (если HP столицы = 0, только лидер)\n"
        "• <code>/аннексия</code> — Захватить территорию врага (если HP врага &lt; 20%, только лидер)\n"
        "• <code>/ультиматум [цель] [текст]</code> — Отправить ультиматум клану\n\n"
        "<b>🚀 Ракетная программа:</b>\n"
        "• <code>/разработка [баллистика/ядерка]</code> — Вложить 10% золота в разработку (КД 1ч для граждан)\n"
        "• <code>/пуск [баллистика/ядерка] [цель]</code> — Запустить ракету (только лидер)\n\n"
        "<b>🏭 Экономика и Армия:</b>\n"
        "• <code>/мобилизация</code> — Нанять солдат (от 50 до 500). КД: 5ч (только лидер)\n"
        "• <code>/подработка</code> — Произвести ресурсы для клана (армия и золото). КД: 30 мин\n"
        "• <code>/устроится</code> — Заработать 150-300 золота для клана (только участники). КД: 6ч\n"
        "• <code>/тренировка [сила/защита/здоровье]</code> — Улучшить характеристики клана. КД: 24ч\n"
        "• <code>/строй завод [оружейный/финансовый/оборонительный]</code> — Построить завод. КД: 10 мин (только лидер)\n\n"
        "<i>Бот работает в группах! Добавьте его в чат вашего клана.</i>"
    )
    await message.answer(text)

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    text = (
        "👋 <b>Приветствую, полководец!</b>\n\n"
        "Я — Клан-Бот, твой верный помощник в управлении кланом и ведении войн.\n"
        "Чтобы увидеть полный список команд и узнать, как управлять своей империей, введи команду:\n\n"
        "👉 /boevik"
    )
    await message.answer(text)

# --- Clan Management ---

@router.message(F.text.regexp(r'(?i)^/создать клан'))
async def create_clan(message: types.Message):
    args = message.text.split()
    # Expecting: /создать клан Name Tag (at least 4 parts)
    if len(args) < 4:
        await message.answer("⚠️ Использование: <code>/создать клан [название] [тег]</code>")
        return
    
    tag = args[-1]
    name = " ".join(args[2:-1])
    
    if len(tag) > 5:
        await message.answer("⚠️ Тег не должен превышать 5 символов.")
        return

    user_id = str(message.from_user.id)
    username = message.from_user.username or message.from_user.first_name or user_id
    
    user = get_or_create_user(user_id, username)
    if user.get('clan_id'):
        await message.answer("⚠️ Вы уже состоите в клане!")
        return
        
    clans_ref = get_db_ref('clans')
    all_clans = clans_ref.get() or {}
    for cid, cdata in all_clans.items():
        if cdata.get('name', '').lower() == name.lower() or cdata.get('tag', '').lower() == tag.lower():
            await message.answer("⚠️ Клан с таким названием или тегом уже существует.")
            return
            
    new_clan_data = {
        'name': name,
        'tag': tag,
        'leader_id': user_id,
        'chat_id': message.chat.id,
        'exp': 0,
        'capital_hp': 1000,
        'max_capital_hp': 1000,
        'population_limit': 15,
        'gold': 0,
        'power_level': 1,
        'defense_level': 1,
        'health_level': 1,
        'factory_weapon': 0,
        'factory_finance': 0,
        'factory_defense': 0,
        'war_id': None
    }
    
    new_clan_ref = clans_ref.push(new_clan_data)
    clan_id = new_clan_ref.key
    
    get_db_ref(f'users/{user_id}').update({'clan_id': clan_id})
    await message.answer(f"✅ Клан <b>{html.escape(name)}</b> [{html.escape(tag)}] успешно создан!\nВы стали лидером.")

@router.message(Command("вступить", prefix="/"))
async def join_clan(message: types.Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("⚠️ Использование: <code>/вступить [название или тег]</code>")
        return
    query = args[1].lower()
    user_id = str(message.from_user.id)
    username = message.from_user.username or message.from_user.first_name or user_id
    
    user = get_or_create_user(user_id, username)
    if user.get('clan_id'):
        await message.answer("⚠️ Вы уже состоите в клане! Сначала покиньте его (<code>/выйти</code>).")
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
        
    all_users = get_db_ref('users').get() or {}
    members_count = sum(1 for u in all_users.values() if u.get('clan_id') == target_clan_id)
    
    if members_count >= target_clan.get('population_limit', 15):
        await message.answer("⚠️ В клане нет мест! Лидер должен построить больше заводов.")
        return
        
    get_db_ref(f'users/{user_id}').update({'clan_id': target_clan_id})
    await message.answer(f"✅ Вы успешно вступили в клан <b>{html.escape(target_clan['name'])}</b>!")

@router.message(Command("выйти", prefix="/"))
async def leave_clan(message: types.Message):
    user_id = str(message.from_user.id)
    user = get_or_create_user(user_id, message.from_user.username or message.from_user.first_name)
    clan_id = user.get('clan_id')
    
    if not clan_id:
        await message.answer("⚠️ Вы не состоите в клане.")
        return
        
    clan = get_db_ref(f'clans/{clan_id}').get()
    if clan and clan.get('leader_id') == user_id:
        await message.answer("⚠️ Вы лидер клана! Вы не можете просто выйти. Используйте <code>/удалить клан подтверждаю</code>, чтобы распустить клан.")
        return
        
    get_db_ref(f'users/{user_id}').update({'clan_id': None, 'army': 0})
    await message.answer("🚪 Вы покинули клан.")

@router.message(F.text.regexp(r'(?i)^/удалить клан'))
async def delete_clan(message: types.Message):
    args = message.text.split()
    if len(args) < 3 or args[2].lower() != "подтверждаю":
        await message.answer("⚠️ Вы уверены, что хотите удалить клан? Это действие необратимо!\nДля подтверждения введите: <code>/удалить клан подтверждаю</code>")
        return
        
    user_id = str(message.from_user.id)
    user = get_or_create_user(user_id, message.from_user.username or message.from_user.first_name)
    clan_id = user.get('clan_id')
    
    if not clan_id:
        await message.answer("⚠️ Вы не состоите в клане.")
        return
        
    clan = get_db_ref(f'clans/{clan_id}').get()
    if clan.get('leader_id') != user_id:
        await message.answer("⚠️ Только лидер может удалить клан!")
        return
        
    if clan.get('war_id'):
        await message.answer("⚠️ Вы не можете распустить клан во время войны! Сначала заключите мир или капитулируйте.")
        return
        
    # Kick all members
    all_users = get_db_ref('users').get() or {}
    for uid, udata in all_users.items():
        if udata.get('clan_id') == clan_id:
            get_db_ref(f'users/{uid}').update({'clan_id': None, 'army': 0})
            
    # Delete clan
    get_db_ref(f'clans/{clan_id}').delete()
    await message.answer(f"💥 Клан <b>{html.escape(clan.get('name', ''))}</b> был распущен.")

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
        
    # Sort by exp descending
    group_clans.sort(key=lambda x: x.get('exp', 0), reverse=True)
    
    all_users = get_db_ref('users').get() or {}
    
    lines = ["🏆 <b>Кланы этой группы:</b>\n"]
    for i, c in enumerate(group_clans, 1):
        members = sum(1 for u in all_users.values() if u.get('clan_id') == c['id'])
        lines.append(f"{i}. <b>{html.escape(c.get('name', ''))}</b> [{html.escape(c.get('tag', ''))}] — 👥 {members} | 💰 {c.get('gold', 0)} | 🌟 {c.get('exp', 0)}")
        
    await message.answer("\n".join(lines))

@router.message(F.text.regexp(r'(?i)^/мой клан'))
async def my_clan(message: types.Message):
    user_id = str(message.from_user.id)
    user = get_or_create_user(user_id, message.from_user.username or message.from_user.first_name)
    clan_id = user.get('clan_id')
    
    if not clan_id:
        await message.answer("⚠️ Вы не состоите в клане.")
        return
        
    clan = get_db_ref(f'clans/{clan_id}').get()
    if not clan:
        await message.answer("⚠️ Ваш клан не найден (возможно, был удален).")
        get_db_ref(f'users/{user_id}').update({'clan_id': None})
        return
        
    # Update chat_id to ensure notifications go to the current active chat
    if clan.get('chat_id') != message.chat.id:
        get_db_ref(f'clans/{clan_id}').update({'chat_id': message.chat.id})
        
    all_users = get_db_ref('users').get() or {}
    clan_users = [u for u in all_users.values() if u.get('clan_id') == clan_id]
    members_count = len(clan_users)
    total_army = sum(u.get('army', 0) for u in clan_users)
    total_def = sum(u.get('defense_army', 0) for u in clan_users)
    
    war_status = "Мир 🕊"
    if clan.get('war_id'):
        war_status = "ВОЙНА ⚔️"
        
    all_clans = get_db_ref('clans').get() or {}
    allies = clan.get('allies', [])
    allies_text = "Нет"
    if allies:
        ally_names = [html.escape(all_clans.get(aid, {}).get('name', 'Неизвестно')) for aid in allies if aid in all_clans]
        allies_text = ", ".join(ally_names) if ally_names else "Нет"
        
    text = (
        f"🛡 <b>Клан:</b> {html.escape(clan.get('name', ''))} [{html.escape(clan.get('tag', ''))}]\n"
        f"👑 <b>Лидер:</b> <a href='tg://user?id={clan.get('leader_id')}'>Лидер</a>\n"
        f"👥 <b>Участники:</b> {members_count} / {clan.get('population_limit', 15)}\n"
        f"⚔️ <b>Армия клана:</b> {total_army} (В обороне: {total_def})\n"
        f"🏰 <b>Столица:</b> {clan.get('capital_hp', 1000)} / {clan.get('max_capital_hp', 1000)} HP\n"
        f"💰 <b>Золото:</b> {clan.get('gold', 0)}\n"
        f"🌟 <b>Опыт:</b> {clan.get('exp', 0)}\n"
        f"🤝 <b>Союзники:</b> {allies_text}\n"
        f"📊 <b>Статус:</b> {war_status}\n\n"
        f"<b>📈 Уровни:</b>\n"
        f"💪 Сила: {clan.get('power_level', 1)} | 🛡 Защита: {clan.get('defense_level', 1)} | ❤️ Здоровье: {clan.get('health_level', 1)}\n\n"
        f"<b>🏭 Заводы:</b>\n"
        f"🔫 Оружейные: {clan.get('factory_weapon', 0)} | 🏦 Финансовые: {clan.get('factory_finance', 0)} | 🧱 Оборонительные: {clan.get('factory_defense', 0)}\n\n"
        f"<b>🚀 Ракетная программа:</b>\n"
        f"Баллистика: {clan.get('prog_ballistic', 0)} / 100000\n"
        f"Ядерка: {clan.get('prog_nuclear', 0)} / 1000000"
    )
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🧹 Подработка", callback_data=f"c_work_{user_id}")
    builder.button(text="🚀 Ракеты", callback_data=f"c_rocket_menu_{user_id}")
    
    if clan.get('leader_id') != user_id:
        builder.button(text="🏢 Устроиться", callback_data=f"c_job_{user_id}")
        builder.button(text="🚪 Выйти", callback_data=f"c_leave_{user_id}")
    else:
        builder.button(text="⚔️ Мобилизация", callback_data=f"c_mob_{user_id}")
        builder.button(text="💪 Тренировка", callback_data=f"c_train_menu_{user_id}")
        builder.button(text="🏭 Завод", callback_data=f"c_factory_menu_{user_id}")
        builder.button(text="💥 Распустить", callback_data=f"c_delete_menu_{user_id}")
        
    builder.adjust(2)
    await message.answer(text, reply_markup=builder.as_markup())

# --- Economy & Army ---

@router.message(Command("мобилизация", prefix="/"))
async def mobilize(message: types.Message):
    user_id = str(message.from_user.id)
    user = get_or_create_user(user_id, message.from_user.username or message.from_user.first_name)
    clan_id = user.get('clan_id')
    if not clan_id:
        await message.answer("⚠️ Вы не состоите в клане.")
        return
        
    clan = get_db_ref(f'clans/{clan_id}').get()
    if clan.get('leader_id') != user_id:
        await message.answer("⚠️ Только лидер может проводить мобилизацию!")
        return
        
    now = datetime.now()
    if user.get('last_mobilization'):
        last_mob = datetime.fromisoformat(user['last_mobilization'])
        if now - last_mob < timedelta(hours=5):
            rem = timedelta(hours=5) - (now - last_mob)
            await message.answer(f"⏳ КД на мобилизацию! Осталось: {rem.seconds//3600}ч {(rem.seconds//60)%60}м")
            return
            
    amount = random.randint(50, 500)
    new_army = user.get('army', 0) + amount
    get_db_ref(f'users/{user_id}').update({
        'army': new_army,
        'last_mobilization': now.isoformat()
    })
    await message.answer(f"⚔️ Вы успешно мобилизовали {amount} солдат в армию клана!")

@router.message(Command("подработка", prefix="/"))
async def work(message: types.Message):
    user_id = str(message.from_user.id)
    user = get_or_create_user(user_id, message.from_user.username or message.from_user.first_name)
    clan_id = user.get('clan_id')
    if not clan_id:
        await message.answer("⚠️ Вы не состоите в клане.")
        return
        
    now = datetime.now()
    if user.get('last_work'):
        last_work = datetime.fromisoformat(user.get('last_work'))
        if now - last_work < timedelta(minutes=30):
            rem = timedelta(minutes=30) - (now - last_work)
            await message.answer(f"⏳ Вы устали! Следующая смена через: {rem.seconds//60}м")
            return
            
    army_gain = random.randint(10, 50)
    gold_gain = random.randint(100, 200)
    
    new_army = user.get('army', 0) + army_gain
    get_db_ref(f'users/{user_id}').update({
        'army': new_army,
        'last_work': now.isoformat()
    })
    
    clan_ref = get_db_ref(f'clans/{clan_id}')
    clan = clan_ref.get()
    new_gold = clan.get('gold', 0) + gold_gain
    clan_ref.update({'gold': new_gold})
    
    await message.answer(f"🏭 Вы поработали на благо клана!\nПроизведено солдат: {army_gain}\nЗаработано золота: {gold_gain}")

@router.message(Command("устроится", "устроиться", prefix="/"))
async def get_job(message: types.Message):
    user_id = str(message.from_user.id)
    user = get_or_create_user(user_id, message.from_user.username or message.from_user.first_name)
    clan_id = user.get('clan_id')
    if not clan_id:
        await message.answer("⚠️ Вы не состоите в клане.")
        return
        
    clan_ref = get_db_ref(f'clans/{clan_id}')
    clan = clan_ref.get()
    if clan.get('leader_id') == user_id:
        await message.answer("⚠️ Лидер не может устроиться на работу!")
        return
        
    now = datetime.now()
    if user.get('last_job'):
        last_job = datetime.fromisoformat(user.get('last_job'))
        if now - last_job < timedelta(hours=6):
            rem = timedelta(hours=6) - (now - last_job)
            await message.answer(f"⏳ Вы уже работаете! Следующая зарплата через: {rem.seconds//3600}ч {(rem.seconds//60)%60}м")
            return
            
    gold_gain = random.randint(150, 300)
    
    get_db_ref(f'users/{user_id}').update({
        'last_job': now.isoformat()
    })
    
    new_gold = clan.get('gold', 0) + gold_gain
    clan_ref.update({'gold': new_gold})
    
    await message.answer(f"🏢 Вы устроились на работу и принесли в казну клана <b>{gold_gain}</b> золота!")

@router.message(Command("тренировка", prefix="/"))
async def train(message: types.Message):
    args = message.text.split()
    valid_stats = ['сила', 'защита', 'здоровье']
    if len(args) < 2 or args[1].lower() not in valid_stats:
        await message.answer("⚠️ Использование: <code>/тренировка [сила/защита/здоровье]</code>")
        return
    stat = args[1].lower()
    
    user_id = str(message.from_user.id)
    user = get_or_create_user(user_id, message.from_user.username or message.from_user.first_name)
    clan_id = user.get('clan_id')
    if not clan_id:
        await message.answer("⚠️ Вы не состоите в клане.")
        return
        
    now = datetime.now()
    if user.get('last_train'):
        last_train = datetime.fromisoformat(user['last_train'])
        if now - last_train < timedelta(hours=24):
            rem = timedelta(hours=24) - (now - last_train)
            await message.answer(f"⏳ КД на тренировку! Осталось: {rem.seconds//3600}ч {(rem.seconds//60)%60}м")
            return
            
    field = ""
    if stat == 'сила': field = 'power_level'
    elif stat == 'защита': field = 'defense_level'
    elif stat == 'здоровье': field = 'health_level'
    
    clan_ref = get_db_ref(f'clans/{clan_id}')
    clan = clan_ref.get()
    new_level = clan.get(field, 1) + 1
    
    clan_ref.update({field: new_level})
    get_db_ref(f'users/{user_id}').update({'last_train': now.isoformat()})
    
    await message.answer(f"💪 Вы успешно потренировали клан! Навык <b>{stat}</b> повышен до {new_level}.")

@router.message(F.text.regexp(r'(?i)^/строй завод'))
async def build_factory(message: types.Message):
    args = message.text.split()
    # Expecting: /строй завод type
    valid_types = ['оружейный', 'финансовый', 'оборонительный']
    if len(args) < 3 or args[2].lower() not in valid_types:
        await message.answer("⚠️ Использование: <code>/строй завод [оружейный/финансовый/оборонительный]</code>")
        return
    ftype = args[2].lower()
    
    user_id = str(message.from_user.id)
    user = get_or_create_user(user_id, message.from_user.username or message.from_user.first_name)
    clan_id = user.get('clan_id')
    if not clan_id:
        await message.answer("⚠️ Вы не состоите в клане.")
        return
        
    clan_ref = get_db_ref(f'clans/{clan_id}')
    clan = clan_ref.get()
    
    if clan.get('leader_id') != user_id:
        await message.answer("⚠️ Только лидер может строить заводы!")
        return
        
    now = datetime.now()
    if user.get('last_factory'):
        last_fac = datetime.fromisoformat(user['last_factory'])
        if now - last_fac < timedelta(minutes=10):
            rem = timedelta(minutes=10) - (now - last_fac)
            await message.answer(f"⏳ КД на постройку! Осталось: {rem.seconds//60}м")
            return
            
    field = ""
    if ftype == 'оружейный': field = 'factory_weapon'
    elif ftype == 'финансовый': field = 'factory_finance'
    elif ftype == 'оборонительный': field = 'factory_defense'
    
    new_factory_count = clan.get(field, 0) + 1
    new_pop_limit = clan.get('population_limit', 15) + 1
    
    clan_ref.update({
        field: new_factory_count,
        'population_limit': new_pop_limit
    })
    get_db_ref(f'users/{user_id}').update({'last_factory': now.isoformat()})
    
    await message.answer(f"🏭 Вы успешно построили <b>{ftype}</b> завод! Лимит населения увеличен на 1.")

# --- War System ---

@router.message(F.text.regexp(r'(?i)^/объявить войну'))
async def declare_war(message: types.Message):
    args = message.text.split(maxsplit=2)
    # Expecting: /объявить войну Target
    if len(args) < 3:
        await message.answer("⚠️ Использование: <code>/объявить войну [название или тег клана]</code>")
        return
    target_query = args[2].lower()
    
    user_id = str(message.from_user.id)
    user = get_or_create_user(user_id, message.from_user.username or message.from_user.first_name)
    attacker_id = user.get('clan_id')
    
    if not attacker_id:
        await message.answer("⚠️ Вы не состоите в клане.")
        return
        
    attacker = get_db_ref(f'clans/{attacker_id}').get()
    if attacker.get('leader_id') != user_id:
        await message.answer("⚠️ Только лидер может объявлять войну!")
        return
        
    if attacker.get('war_id'):
        await message.answer("⚠️ Ваш клан уже участвует в войне!")
        return
        
    all_clans = get_db_ref('clans').get() or {}
    defender_id = None
    defender = None
    for cid, cdata in all_clans.items():
        if cdata.get('name', '').lower() == target_query or cdata.get('tag', '').lower() == target_query:
            defender_id = cid
            defender = cdata
            break
            
    if not defender:
        await message.answer("⚠️ Клан противника не найден.")
        return
        
    if defender_id == attacker_id:
        await message.answer("⚠️ Нельзя объявить войну самому себе.")
        return
        
    if defender_id in attacker.get('allies', []):
        await message.answer("⚠️ Вы не можете объявить войну своему союзнику! Сначала разорвите альянс.")
        return
        
    if defender.get('war_id'):
        await message.answer("⚠️ Этот клан уже с кем-то воюет.")
        return
        
    now = datetime.now().isoformat()
    war_data = {
        'attacker_id': attacker_id,
        'defender_id': defender_id,
        'start_time': now,
        'last_tick': now,
        'white_peace_offer': None
    }
    
    new_war_ref = get_db_ref('wars').push(war_data)
    war_id = new_war_ref.key
    
    get_db_ref(f'clans/{attacker_id}').update({'war_id': war_id})
    get_db_ref(f'clans/{defender_id}').update({'war_id': war_id})
    
    await message.answer(f"⚔️ Клан <b>{html.escape(attacker['name'])}</b> объявил войну клану <b>{html.escape(defender['name'])}</b>!\nГотовьтесь к битвам!")

@router.message(F.text.regexp(r'(?i)^/белый мир'))
async def white_peace(message: types.Message):
    user_id = str(message.from_user.id)
    user = get_or_create_user(user_id, message.from_user.username or message.from_user.first_name)
    clan_id = user.get('clan_id')
    if not clan_id: return
    
    clan = get_db_ref(f'clans/{clan_id}').get()
    if clan.get('leader_id') != user_id:
        await message.answer("⚠️ Только лидер может предлагать мир.")
        return
        
    war_id = clan.get('war_id')
    if not war_id:
        await message.answer("⚠️ Ваш клан не воюет.")
        return
        
    war_ref = get_db_ref(f'wars/{war_id}')
    war = war_ref.get()
    if not war: return
    
    if war.get('white_peace_offer') == clan_id:
        await message.answer("⏳ Вы уже предложили белый мир. Ожидайте ответа.")
        return
        
    if war.get('white_peace_offer') and war.get('white_peace_offer') != clan_id:
        # Accept peace
        att_id = war['attacker_id']
        def_id = war['defender_id']
        
        for cid in [att_id, def_id]:
            cdata = get_db_ref(f'clans/{cid}').get()
            new_exp = max(0, int(cdata.get('exp', 0) * 0.85))
            get_db_ref(f'clans/{cid}').update({'war_id': None, 'exp': new_exp})
            
        war_ref.delete()
        await message.answer("🤝 Белый мир заключён! Оба клана потеряли 15% опыта.")
    else:
        # Offer peace
        war_ref.update({'white_peace_offer': clan_id})
        await message.answer("🕊 Вы предложили белый мир. Чтобы он вступил в силу, лидер вражеского клана должен также написать <code>/белый мир</code>.")

@router.message(Command("капитуляция", prefix="/"))
async def capitulate(message: types.Message):
    user_id = str(message.from_user.id)
    user = get_or_create_user(user_id, message.from_user.username or message.from_user.first_name)
    clan_id = user.get('clan_id')
    if not clan_id: return
    
    clan = get_db_ref(f'clans/{clan_id}').get()
    if clan.get('leader_id') != user_id:
        await message.answer("⚠️ Только лидер может капитулировать.")
        return
        
    war_id = clan.get('war_id')
    if not war_id:
        await message.answer("⚠️ Ваш клан не воюет.")
        return
        
    if clan.get('capital_hp', 1000) > 0:
        await message.answer("⚠️ Капитуляция доступна только если здоровье вашей столицы равно 0!")
        return
        
    war_ref = get_db_ref(f'wars/{war_id}')
    war = war_ref.get()
    if not war: return
    
    winner_id = war['attacker_id'] if war['defender_id'] == clan_id else war['defender_id']
    
    # Apply capitulation effects
    new_exp = max(0, int(clan.get('exp', 0) * 0.5))
    new_fw = max(0, clan.get('factory_weapon', 0) - 1)
    new_ff = max(0, clan.get('factory_finance', 0) - 1)
    
    stolen_gold = int(clan.get('gold', 0) * 0.3)
    new_gold = clan.get('gold', 0) - stolen_gold
    
    get_db_ref(f'clans/{clan_id}').update({
        'exp': new_exp,
        'factory_weapon': new_fw,
        'factory_finance': new_ff,
        'war_id': None,
        'capital_hp': clan.get('max_capital_hp', 1000),
        'gold': new_gold
    })
    
    winner = get_db_ref(f'clans/{winner_id}').get()
    get_db_ref(f'clans/{winner_id}').update({
        'gold': winner.get('gold', 0) + stolen_gold,
        'war_id': None
    })
    
    war_ref.delete()
    await message.answer(f"🏳️ Ваш клан капитулировал! Вы потеряли 50% опыта, часть заводов и {stolen_gold} золота.")

@router.message(Command("аннексия", prefix="/"))
async def annex(message: types.Message):
    user_id = str(message.from_user.id)
    user = get_or_create_user(user_id, message.from_user.username or message.from_user.first_name)
    clan_id = user.get('clan_id')
    if not clan_id: return
    
    clan = get_db_ref(f'clans/{clan_id}').get()
    if clan.get('leader_id') != user_id:
        await message.answer("⚠️ Только лидер может проводить аннексию.")
        return
        
    war_id = clan.get('war_id')
    if not war_id:
        await message.answer("⚠️ Ваш клан не воюет.")
        return
        
    war_ref = get_db_ref(f'wars/{war_id}')
    war = war_ref.get()
    if not war: return
    
    loser_id = war['defender_id'] if war['attacker_id'] == clan_id else war['attacker_id']
    loser = get_db_ref(f'clans/{loser_id}').get()
    
    if loser.get('capital_hp', 1000) > loser.get('max_capital_hp', 1000) * 0.2:
        await message.answer("⚠️ Аннексия доступна только если здоровье вражеской столицы ниже 20%!")
        return
        
    # Apply annexation effects
    new_exp = max(0, int(loser.get('exp', 0) * 0.75))
    stolen_gold = int(loser.get('gold', 0) * 0.2)
    
    get_db_ref(f'clans/{loser_id}').update({
        'exp': new_exp,
        'capital_hp': int(loser.get('max_capital_hp', 1000) / 2),
        'war_id': None,
        'gold': loser.get('gold', 0) - stolen_gold
    })
    
    get_db_ref(f'clans/{clan_id}').update({
        'gold': clan.get('gold', 0) + stolen_gold,
        'war_id': None,
        'population_limit': clan.get('population_limit', 15) + 1
    })
    
    # Transfer some users
    all_users = get_db_ref('users').get() or {}
    loser_users = [uid for uid, u in all_users.items() if u.get('clan_id') == loser_id]
    transfer_count = int(len(loser_users) * 0.3)
    
    for i in range(transfer_count):
        get_db_ref(f'users/{loser_users[i]}').update({'clan_id': clan_id})
        
    war_ref.delete()
    await message.answer(f"⚔️ Вы успешно аннексировали часть территории клана <b>{html.escape(loser.get('name', ''))}</b>! Получено золото и новые участники.")

@router.message(F.text.regexp(r'(?i)^/атака'))
async def attack(message: types.Message):
    args = message.text.split()
    if len(args) < 2 or not args[1].isdigit():
        await message.answer("⚠️ Использование: <code>/атака [количество]</code>")
        return
    
    amount = int(args[1])
    if amount <= 0:
        return
        
    user_id = str(message.from_user.id)
    user = get_or_create_user(user_id, message.from_user.username or message.from_user.first_name)
    clan_id = user.get('clan_id')
    
    if not clan_id:
        await message.answer("⚠️ Вы не состоите в клане.")
        return
        
    if user.get('army', 0) < amount:
        await message.answer("⚠️ У вас недостаточно солдат.")
        return
        
    if user.get('army', 0) <= 0:
        await message.answer("⚠️ У вас нет армии для атаки.")
        return
        
    clan = get_db_ref(f'clans/{clan_id}').get()
    war_id = clan.get('war_id')
    if not war_id:
        await message.answer("⚠️ Ваш клан не воюет.")
        return
        
    war_ref = get_db_ref(f'wars/{war_id}')
    war = war_ref.get()
    if not war: return
    
    # Check truce
    truce_until = war.get('truce_until')
    if truce_until:
        truce_time = datetime.fromisoformat(truce_until)
        if datetime.now() < truce_time:
            await message.answer("⚠️ Действует перемирие! Атака невозможна.")
            return
            
    # Check cooldown
    now = datetime.now()
    if user.get('last_attack'):
        last_attack = datetime.fromisoformat(user['last_attack'])
        if now - last_attack < timedelta(minutes=3):
            rem = timedelta(minutes=3) - (now - last_attack)
            await message.answer(f"⏳ КД на атаку! Осталось: {rem.seconds} сек.")
            return
            
    # Deduct army and set cooldown
    get_db_ref(f'users/{user_id}').update({
        'army': user.get('army', 0) - amount,
        'last_attack': now.isoformat()
    })
    
    delay = random.randint(10, 40)
    await message.answer(f"⚔️ Войска отправлены в бой! ({amount} солдат). Ожидайте результатов через {delay} секунд...")
    
    await asyncio.sleep(delay)
    
    # Recalculate everything
    clan = get_db_ref(f'clans/{clan_id}').get()
    war = get_db_ref(f'wars/{war_id}').get()
    if not war:
        await message.answer("⚠️ Война уже закончилась, ваши войска вернулись.")
        get_db_ref(f'users/{user_id}').update({'army': user.get('army', 0) + amount})
        return
        
    defender_id = war['defender_id'] if war['attacker_id'] == clan_id else war['attacker_id']
    defender = get_db_ref(f'clans/{defender_id}').get()
    
    # Calculate power
    att_power = amount * clan.get('power_level', 1) * (1 + 0.05 * clan.get('factory_weapon', 0))
    
    all_users = get_db_ref('users').get() or {}
    def_army_reg = sum(u.get('army', 0) for u in all_users.values() if u.get('clan_id') == defender_id)
    def_army_def = sum(u.get('defense_army', 0) for u in all_users.values() if u.get('clan_id') == defender_id)
    def_army_total = def_army_reg + def_army_def
    
    def_power = (def_army_reg + def_army_def * 1.5) * defender.get('defense_level', 1) * (1 + 0.05 * defender.get('factory_defense', 0)) * 0.1
    
    # Calculate losses
    att_losses = min(amount, int((def_power / att_power) * amount * random.uniform(0.5, 1.5)) if att_power > 0 else amount)
    def_losses = min(int(def_army_total * 0.1), int((att_power / def_power) * (def_army_total * 0.1) * random.uniform(0.5, 1.5)) if def_power > 0 else int(att_power))
    
    damage = max(0, int(att_power - def_power))
    
    # Apply defender losses proportionally
    if def_losses > 0 and def_army_total > 0:
        loss_ratio = def_losses / def_army_total
        for uid, udata in all_users.items():
            if udata.get('clan_id') == defender_id:
                u_reg = udata.get('army', 0)
                u_def = udata.get('defense_army', 0)
                if u_reg > 0 or u_def > 0:
                    reg_loss = int(u_reg * loss_ratio)
                    def_loss = int(u_def * loss_ratio * 0.5) # Defense takes half losses
                    get_db_ref(f'users/{uid}').update({
                        'army': max(0, u_reg - reg_loss),
                        'defense_army': max(0, u_def - def_loss)
                    })
                
    # Return surviving attackers
    survivors = amount - att_losses
    if survivors > 0:
        current_user = get_db_ref(f'users/{user_id}').get()
        get_db_ref(f'users/{user_id}').update({'army': current_user.get('army', 0) + survivors})
        
    # Apply damage to capital
    new_hp = max(0, defender.get('capital_hp', 1000) - damage)
    get_db_ref(f'clans/{defender_id}').update({'capital_hp': new_hp})
    
    notes = [
        "Разведка докладывает о жестоких боях на границе.",
        "Небо заволокло дымом от горящих заводов.",
        "Солдаты сражались до последней капли крови.",
        "Враг был застигнут врасплох, но быстро организовал оборону.",
        "Артиллерия не умолкала ни на минуту."
    ]
    note = random.choice(notes)
    
    result_msg = (
        f"🔥 <b>Итог битвы:</b>\n"
        f"<i>{note}</i>\n\n"
        f"Атакующий <b>{html.escape(clan.get('name', ''))}</b>:\n"
        f"➖ Потери: {att_losses} солдат\n\n"
        f"Обороняющийся <b>{html.escape(defender.get('name', ''))}</b>:\n"
        f"➖ Потери: {def_losses} солдат\n"
        f"💥 Урон столице: {damage} (Осталось: {new_hp} HP)\n\n"
        f"<i>«Столица близкая...»</i>"
    )
    
    await message.answer(result_msg)
    
    # Notify defender
    def_chat_id = defender.get('chat_id')
    if def_chat_id:
        try:
            await message.bot.send_message(def_chat_id, f"⚠️ <b>Внимание!</b> Нас атаковали!\n\n{result_msg}")
        except:
            pass

@router.message(F.text.regexp(r'(?i)^/перемирие'))
async def truce(message: types.Message):
    args = message.text.split()
    if len(args) < 2:
        await message.answer("⚠️ Использование: <code>/перемирие [время, например 1ч или 1д]</code>")
        return
        
    time_str = args[1].lower()
    hours = 0
    if 'ч' in time_str:
        hours = int(re.sub(r'\D', '', time_str) or 0)
    elif 'д' in time_str:
        hours = int(re.sub(r'\D', '', time_str) or 0) * 24
        
    if hours <= 0:
        await message.answer("⚠️ Неверный формат времени.")
        return
        
    user_id = str(message.from_user.id)
    user = get_or_create_user(user_id, message.from_user.username or message.from_user.first_name)
    clan_id = user.get('clan_id')
    if not clan_id: return
    
    clan = get_db_ref(f'clans/{clan_id}').get()
    if clan.get('leader_id') != user_id:
        await message.answer("⚠️ Только лидер может предлагать перемирие.")
        return
        
    war_id = clan.get('war_id')
    if not war_id:
        await message.answer("⚠️ Ваш клан не воюет.")
        return
        
    war_ref = get_db_ref(f'wars/{war_id}')
    war = war_ref.get()
    
    if war.get('truce_offer_by') == clan_id:
        await message.answer("⏳ Вы уже предложили перемирие. Ожидайте ответа.")
        return
        
    if war.get('truce_offer_by') and war.get('truce_offer_by') != clan_id:
        # Accept
        truce_hours = war.get('truce_offer_hours', 1)
        truce_until = (datetime.now() + timedelta(hours=truce_hours)).isoformat()
        war_ref.update({
            'truce_offer_by': None,
            'truce_offer_hours': None,
            'truce_until': truce_until
        })
        await message.answer(f"🤝 Перемирие заключено на {truce_hours} ч.!")
    else:
        # Offer
        war_ref.update({
            'truce_offer_by': clan_id,
            'truce_offer_hours': hours
        })
        await message.answer(f"🕊 Вы предложили перемирие на {hours} ч. Чтобы оно вступило в силу, лидер вражеского клана должен также написать <code>/перемирие {hours}ч</code>.")

@router.message(F.text.regexp(r'(?i)^/разработка'))
async def develop(message: types.Message):
    args = message.text.split()
    if len(args) < 2 or args[1].lower() not in ['баллистика', 'ядерка']:
        await message.answer("⚠️ Использование: <code>/разработка [баллистика/ядерка]</code>")
        return
        
    target = args[1].lower()
    
    user_id = str(message.from_user.id)
    user = get_or_create_user(user_id, message.from_user.username or message.from_user.first_name)
    clan_id = user.get('clan_id')
    if not clan_id: return
    
    clan_ref = get_db_ref(f'clans/{clan_id}')
    clan = clan_ref.get()
    
    # Cooldown for non-leaders
    if clan.get('leader_id') != user_id:
        now = datetime.now()
        if user.get('last_rocket_dev'):
            last_dev = datetime.fromisoformat(user['last_rocket_dev'])
            if now - last_dev < timedelta(hours=1):
                rem = timedelta(hours=1) - (now - last_dev)
                await message.answer(f"⏳ Граждане могут вкладывать в разработку раз в час! Осталось: {rem.seconds//60}м")
                return
        get_db_ref(f'users/{user_id}').update({'last_rocket_dev': now.isoformat()})
    
    gold = clan.get('gold', 0)
    if gold < 10:
        await message.answer("⚠️ В казне слишком мало золота для разработки (нужно хотя бы 10).")
        return
        
    invest = int(gold * 0.1)
    new_gold = gold - invest
    
    if target == 'баллистика':
        prog = clan.get('prog_ballistic', 0) + invest
        clan_ref.update({'gold': new_gold, 'prog_ballistic': prog})
        await message.answer(f"🚀 Вы вложили {invest} золота в баллистику! Прогресс: {prog} / 100000")
    else:
        prog = clan.get('prog_nuclear', 0) + invest
        clan_ref.update({'gold': new_gold, 'prog_nuclear': prog})
        await message.answer(f"☢️ Вы вложили {invest} золота в ядерную программу! Прогресс: {prog} / 1000000")

@router.message(F.text.regexp(r'(?i)^/пуск'))
async def launch(message: types.Message):
    args = message.text.split(maxsplit=2)
    if len(args) < 3 or args[1].lower() not in ['баллистика', 'ядерка']:
        await message.answer("⚠️ Использование: <code>/пуск [баллистика/ядерка] [цель]</code>")
        return
        
    target_type = args[1].lower()
    target_query = args[2].lower()
    
    user_id = str(message.from_user.id)
    user = get_or_create_user(user_id, message.from_user.username or message.from_user.first_name)
    clan_id = user.get('clan_id')
    if not clan_id: return
    
    clan_ref = get_db_ref(f'clans/{clan_id}')
    clan = clan_ref.get()
    
    if clan.get('leader_id') != user_id:
        await message.answer("⚠️ Только лидер может запускать ракеты!")
        return
        
    if target_type == 'баллистика' and clan.get('prog_ballistic', 0) < 100000:
        await message.answer("⚠️ Баллистическая ракета еще не разработана!")
        return
    if target_type == 'ядерка' and clan.get('prog_nuclear', 0) < 1000000:
        await message.answer("⚠️ Ядерная ракета еще не разработана!")
        return
        
    all_clans = get_db_ref('clans').get() or {}
    defender_id = None
    defender = None
    for cid, cdata in all_clans.items():
        if cdata.get('name', '').lower() == target_query or cdata.get('tag', '').lower() == target_query:
            defender_id = cid
            defender = cdata
            break
            
    if not defender:
        await message.answer("⚠️ Цель не найдена.")
        return
        
    if defender_id == clan_id:
        await message.answer("⚠️ Нельзя ударить по себе.")
        return
        
    # Reset progress after launch
    if target_type == 'баллистика':
        clan_ref.update({'prog_ballistic': 0})
        damage = 5000
        msg_text = f"🚀 <b>ЗАПУСК БАЛЛИСТИЧЕСКОЙ РАКЕТЫ!</b>\nКлан <b>{html.escape(clan.get('name', ''))}</b> нанес удар по <b>{html.escape(defender.get('name', ''))}</b>!\nУрон столице: {damage} HP."
    else:
        clan_ref.update({'prog_nuclear': 0})
        damage = 50000
        msg_text = f"☢️ <b>ЯДЕРНЫЙ УДАР!</b>\nКлан <b>{html.escape(clan.get('name', ''))}</b> стер с лица земли <b>{html.escape(defender.get('name', ''))}</b>!\nУрон столице: {damage} HP."
        
    new_hp = max(0, defender.get('capital_hp', 1000) - damage)
    get_db_ref(f'clans/{defender_id}').update({'capital_hp': new_hp})
    
    await message.answer(msg_text)
    
    def_chat_id = defender.get('chat_id')
    if def_chat_id:
        try:
            await message.bot.send_message(def_chat_id, msg_text)
        except:
            pass

@router.message(F.text.regexp(r'(?i)^/ультиматум'))
async def ultimatum(message: types.Message):
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        await message.answer("⚠️ Использование: <code>/ультиматум [название или тег] [сообщение]</code>")
        return
        
    target_query = args[1].lower()
    ult_text = args[2]
    
    user_id = str(message.from_user.id)
    user = get_or_create_user(user_id, message.from_user.username or message.from_user.first_name)
    clan_id = user.get('clan_id')
    if not clan_id: return
    
    clan = get_db_ref(f'clans/{clan_id}').get()
    if clan.get('leader_id') != user_id:
        await message.answer("⚠️ Только лидер может отправлять ультиматумы.")
        return
        
    all_clans = get_db_ref('clans').get() or {}
    defender_id = None
    defender = None
    for cid, cdata in all_clans.items():
        if cdata.get('name', '').lower() == target_query or cdata.get('tag', '').lower() == target_query:
            defender_id = cid
            defender = cdata
            break
            
    if not defender:
        await message.answer("⚠️ Цель не найдена.")
        return
        
    def_chat_id = defender.get('chat_id')
    if not def_chat_id:
        await message.answer("⚠️ Клан не привязан к чату, невозможно отправить ультиматум.")
        return
        
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Принять", callback_data=f"ult_accept_{clan_id}_{defender_id}")
    builder.button(text="❌ Отвергнуть", callback_data=f"ult_reject_{clan_id}_{defender_id}")
    
    try:
        await message.bot.send_message(
            def_chat_id,
            f"📜 <b>УЛЬТИМАТУМ от {html.escape(clan.get('name', ''))}</b> клану <b>{html.escape(defender.get('name', ''))}</b>\n\n<i>{html.escape(ult_text)}</i>\n\nЛидер, сделайте выбор:",
            reply_markup=builder.as_markup()
        )
        await message.answer(f"✅ Ультиматум отправлен клану <b>{html.escape(defender.get('name', ''))}</b>.")
    except Exception as e:
        await message.answer("⚠️ Ошибка отправки ультиматума (возможно, бот не в чате врага).")

@router.callback_query(F.data.startswith("ult_"))
async def ult_callback(callback: types.CallbackQuery):
    parts = callback.data.split('_')
    action = parts[1]
    sender_id = parts[2]
    target_id = parts[3]
    
    user_id = str(callback.from_user.id)
    target_clan = get_db_ref(f'clans/{target_id}').get()
    
    if not target_clan or target_clan.get('leader_id') != user_id:
        await callback.answer("Только лидер может ответить на ультиматум!", show_alert=True)
        return
        
    sender_clan = get_db_ref(f'clans/{sender_id}').get()
    sender_name = sender_clan.get('name', 'Неизвестно') if sender_clan else 'Неизвестно'
    
    if action == "accept":
        text = f"✅ Клан <b>{html.escape(target_clan.get('name', ''))}</b> ПРИНЯЛ ультиматум от <b>{html.escape(sender_name)}</b>!"
    else:
        text = f"❌ Клан <b>{html.escape(target_clan.get('name', ''))}</b> ОТВЕРГ ультиматум от <b>{html.escape(sender_name)}</b>! Готовьтесь к войне!"
        
    await callback.message.edit_text(text)
    
    if sender_clan and sender_clan.get('chat_id'):
        try:
            await callback.bot.send_message(sender_clan.get('chat_id'), text)
        except:
            pass

@router.callback_query(F.data.startswith("ally_"))
async def alliance_callbacks(callback: types.CallbackQuery):
    parts = callback.data.split('_')
    action = parts[1]
    sender_clan_id = parts[2]
    target_clan_id = parts[3]
    user_id = str(callback.from_user.id)
    
    target_clan = get_db_ref(f'clans/{target_clan_id}').get()
    if not target_clan:
        await callback.answer("⚠️ Клан не найден.", show_alert=True)
        return

    if target_clan.get('leader_id') != user_id:
        await callback.answer("⚠️ Только лидер может принимать решения!", show_alert=True)
        return
        
    sender_clan = get_db_ref(f'clans/{sender_clan_id}').get()
    
    if not sender_clan:
        await callback.message.edit_text("⚠️ Один из кланов больше не существует.")
        return
        
    if action == "acc":
        s_allies = sender_clan.get('allies', [])
        t_allies = target_clan.get('allies', [])
        if target_clan_id not in s_allies: s_allies.append(target_clan_id)
        if sender_clan_id not in t_allies: t_allies.append(sender_clan_id)
        
        get_db_ref(f'clans/{sender_clan_id}').update({'allies': s_allies})
        get_db_ref(f'clans/{target_clan_id}').update({'allies': t_allies})
        
        await callback.message.edit_text(f"🤝 Альянс между <b>{html.escape(sender_clan.get('name', ''))}</b> и <b>{html.escape(target_clan.get('name', ''))}</b> заключен!")
        if sender_clan.get('chat_id'):
            try:
                await callback.bot.send_message(sender_clan['chat_id'], f"🤝 Клан <b>{html.escape(target_clan.get('name', ''))}</b> принял ваше предложение об альянсе!")
            except: pass
            
    elif action == "dec":
        await callback.message.edit_text(f"❌ Вы отклонили предложение альянса от <b>{html.escape(sender_clan.get('name', ''))}</b>.")
        if sender_clan.get('chat_id'):
            try:
                await callback.bot.send_message(sender_clan['chat_id'], f"❌ Клан <b>{html.escape(target_clan.get('name', ''))}</b> отклонил ваше предложение об альянсе.")
            except: pass

@router.callback_query(F.data.startswith("c_"))
async def clan_callbacks(callback: types.CallbackQuery):
    parts = callback.data.split('_')
    target_user_id = parts[-1]
    user_id = str(callback.from_user.id)
    
    if user_id != target_user_id:
        await callback.answer("⚠️ Это меню не для вас!", show_alert=True)
        return
        
    action = "_".join(parts[1:-1])
    
    user = get_or_create_user(user_id, callback.from_user.username or callback.from_user.first_name)
    clan_id = user.get('clan_id')
    
    if not clan_id:
        await callback.answer("⚠️ Вы не состоите в клане.", show_alert=True)
        return
        
    clan_ref = get_db_ref(f'clans/{clan_id}')
    clan = clan_ref.get()
    if not clan:
        await callback.answer("⚠️ Ваш клан не найден.", show_alert=True)
        return
        
    is_leader = clan.get('leader_id') == user_id
    now = datetime.now()
    
    if action == "mob":
        if user.get('last_mobilization'):
            last_mob = datetime.fromisoformat(user['last_mobilization'])
            if now - last_mob < timedelta(hours=5):
                rem = timedelta(hours=5) - (now - last_mob)
                await callback.answer(f"⏳ КД на мобилизацию! Осталось: {rem.seconds//3600}ч {(rem.seconds//60)%60}м", show_alert=True)
                return
                
        amount = random.randint(50, 500)
        new_army = user.get('army', 0) + amount
        get_db_ref(f'users/{user_id}').update({
            'army': new_army,
            'last_mobilization': now.isoformat()
        })
        await callback.answer(f"⚔️ Вы успешно мобилизовали {amount} солдат!", show_alert=True)
        
    elif action == "work":
        if user.get('last_work'):
            last_work = datetime.fromisoformat(user.get('last_work'))
            if now - last_work < timedelta(hours=4):
                rem = timedelta(hours=4) - (now - last_work)
                await callback.answer(f"⏳ Вы устали! Следующая смена через: {rem.seconds//3600}ч {(rem.seconds//60)%60}м", show_alert=True)
                return
                
        army_gain = random.randint(10, 50)
        gold_gain = random.randint(100, 200)
        
        get_db_ref(f'users/{user_id}').update({
            'army': user.get('army', 0) + army_gain,
            'last_work': now.isoformat()
        })
        
        clan_ref.update({'gold': clan.get('gold', 0) + gold_gain})
        await callback.answer(f"🏭 Вы поработали!\nПроизведено солдат: {army_gain}\nЗаработано золота: {gold_gain}", show_alert=True)
        
    elif action == "job":
        if is_leader:
            await callback.answer("⚠️ Лидер не может устроиться на работу!", show_alert=True)
            return
            
        if user.get('last_job'):
            last_job = datetime.fromisoformat(user.get('last_job'))
            if now - last_job < timedelta(hours=12):
                rem = timedelta(hours=12) - (now - last_job)
                await callback.answer(f"⏳ Вы уже работаете! Зарплата через: {rem.seconds//3600}ч {(rem.seconds//60)%60}м", show_alert=True)
                return
                
        gold_gain = random.randint(150, 300)
        get_db_ref(f'users/{user_id}').update({'last_job': now.isoformat()})
        clan_ref.update({'gold': clan.get('gold', 0) + gold_gain})
        await callback.answer(f"🏢 Вы принесли в казну клана {gold_gain} золота!", show_alert=True)
        
    elif action == "leave":
        if is_leader:
            await callback.answer("⚠️ Вы лидер клана! Вы не можете просто выйти.", show_alert=True)
            return
        get_db_ref(f'users/{user_id}').update({'clan_id': None, 'army': 0})
        await callback.message.edit_text("🚪 Вы покинули клан.")
        
    elif action == "train_menu":
        if not is_leader:
            await callback.answer("⚠️ Только лидер!", show_alert=True)
            return
        builder = InlineKeyboardBuilder()
        builder.button(text="💪 Сила", callback_data=f"c_train_сила_{user_id}")
        builder.button(text="🛡 Защита", callback_data=f"c_train_защита_{user_id}")
        builder.button(text="❤️ Здоровье", callback_data=f"c_train_здоровье_{user_id}")
        builder.button(text="🔙 Назад", callback_data=f"c_back_{user_id}")
        builder.adjust(1)
        await callback.message.edit_reply_markup(reply_markup=builder.as_markup())
        
    elif action.startswith("train_"):
        if not is_leader:
            await callback.answer("⚠️ Только лидер!", show_alert=True)
            return
        stat = action.split("_")[1]
        if user.get('last_train'):
            last_train = datetime.fromisoformat(user['last_train'])
            if now - last_train < timedelta(hours=24):
                rem = timedelta(hours=24) - (now - last_train)
                await callback.answer(f"⏳ КД на тренировку! Осталось: {rem.seconds//3600}ч {(rem.seconds//60)%60}м", show_alert=True)
                return
                
        field = ""
        if stat == 'сила': field = 'power_level'
        elif stat == 'защита': field = 'defense_level'
        elif stat == 'здоровье': field = 'health_level'
        
        new_level = clan.get(field, 1) + 1
        clan_ref.update({field: new_level})
        get_db_ref(f'users/{user_id}').update({'last_train': now.isoformat()})
        await callback.answer(f"💪 Навык {stat} повышен до {new_level}!", show_alert=True)
        
    elif action == "factory_menu":
        if not is_leader:
            await callback.answer("⚠️ Только лидер!", show_alert=True)
            return
        builder = InlineKeyboardBuilder()
        builder.button(text="🔫 Оружейный", callback_data=f"c_build_оружейный_{user_id}")
        builder.button(text="🏦 Финансовый", callback_data=f"c_build_финансовый_{user_id}")
        builder.button(text="🧱 Оборонительный", callback_data=f"c_build_оборонительный_{user_id}")
        builder.button(text="🔙 Назад", callback_data=f"c_back_{user_id}")
        builder.adjust(1)
        await callback.message.edit_reply_markup(reply_markup=builder.as_markup())
        
    elif action.startswith("build_"):
        if not is_leader:
            await callback.answer("⚠️ Только лидер!", show_alert=True)
            return
        ftype = action.split("_")[1]
        if user.get('last_factory'):
            last_fac = datetime.fromisoformat(user['last_factory'])
            if now - last_fac < timedelta(minutes=10):
                rem = timedelta(minutes=10) - (now - last_fac)
                await callback.answer(f"⏳ КД на постройку! Осталось: {rem.seconds//60}м", show_alert=True)
                return
                
        field = ""
        if ftype == 'оружейный': field = 'factory_weapon'
        elif ftype == 'финансовый': field = 'factory_finance'
        elif ftype == 'оборонительный': field = 'factory_defense'
        
        new_factory_count = clan.get(field, 0) + 1
        new_pop_limit = clan.get('population_limit', 15) + 1
        
        clan_ref.update({
            field: new_factory_count,
            'population_limit': new_pop_limit
        })
        get_db_ref(f'users/{user_id}').update({'last_factory': now.isoformat()})
        await callback.answer(f"🏭 Построен {ftype} завод! Лимит населения: {new_pop_limit}", show_alert=True)
        
    elif action == "rocket_menu":
        builder = InlineKeyboardBuilder()
        builder.button(text="🚀 Разработка Баллистики", callback_data=f"c_dev_баллистика_{user_id}")
        builder.button(text="☢️ Разработка Ядерки", callback_data=f"c_dev_ядерка_{user_id}")
        builder.button(text="🔙 Назад", callback_data=f"c_back_{user_id}")
        builder.adjust(1)
        await callback.message.edit_reply_markup(reply_markup=builder.as_markup())
        
    elif action.startswith("dev_"):
        if not is_leader:
            if user.get('last_rocket_dev'):
                last_dev = datetime.fromisoformat(user['last_rocket_dev'])
                if now - last_dev < timedelta(hours=1):
                    rem = timedelta(hours=1) - (now - last_dev)
                    await callback.answer(f"⏳ КД на разработку! Осталось: {rem.seconds//60}м", show_alert=True)
                    return
            get_db_ref(f'users/{user_id}').update({'last_rocket_dev': now.isoformat()})
            
        target = action.split("_")[1]
        gold = clan.get('gold', 0)
        if gold < 10:
            await callback.answer("⚠️ В казне слишком мало золота (нужно хотя бы 10).", show_alert=True)
            return
            
        invest = int(gold * 0.1)
        new_gold = gold - invest
        
        if target == 'баллистика':
            prog = clan.get('prog_ballistic', 0) + invest
            clan_ref.update({'gold': new_gold, 'prog_ballistic': prog})
            await callback.answer(f"🚀 Вложено {invest} золота! Прогресс: {prog} / 100000", show_alert=True)
        else:
            prog = clan.get('prog_nuclear', 0) + invest
            clan_ref.update({'gold': new_gold, 'prog_nuclear': prog})
            await callback.answer(f"☢️ Вложено {invest} золота! Прогресс: {prog} / 1000000", show_alert=True)
            
    elif action == "delete_menu":
        if not is_leader:
            await callback.answer("⚠️ Только лидер!", show_alert=True)
            return
        builder = InlineKeyboardBuilder()
        builder.button(text="💥 ПОДТВЕРДИТЬ УДАЛЕНИЕ", callback_data=f"c_delete_confirm_{user_id}")
        builder.button(text="🔙 Отмена", callback_data=f"c_back_{user_id}")
        builder.adjust(1)
        await callback.message.edit_reply_markup(reply_markup=builder.as_markup())
        
    elif action == "delete_confirm":
        if not is_leader:
            await callback.answer("⚠️ Только лидер!", show_alert=True)
            return
        if clan.get('war_id'):
            await callback.answer("⚠️ Вы не можете распустить клан во время войны!", show_alert=True)
            return
            
        all_users = get_db_ref('users').get() or {}
        for uid, udata in all_users.items():
            if udata.get('clan_id') == clan_id:
                get_db_ref(f'users/{uid}').update({'clan_id': None, 'army': 0})
                
        clan_ref.delete()
        await callback.message.edit_text(f"💥 Клан <b>{html.escape(clan.get('name', ''))}</b> был распущен.")
        
    elif action == "back":
        builder = InlineKeyboardBuilder()
        builder.button(text="🧹 Подработка", callback_data=f"c_work_{user_id}")
        builder.button(text="🚀 Ракеты", callback_data=f"c_rocket_menu_{user_id}")
        
        if not is_leader:
            builder.button(text="🏢 Устроиться", callback_data=f"c_job_{user_id}")
            builder.button(text="🚪 Выйти", callback_data=f"c_leave_{user_id}")
        else:
            builder.button(text="⚔️ Мобилизация", callback_data=f"c_mob_{user_id}")
            builder.button(text="💪 Тренировка", callback_data=f"c_train_menu_{user_id}")
            builder.button(text="🏭 Завод", callback_data=f"c_factory_menu_{user_id}")
            builder.button(text="💥 Распустить", callback_data=f"c_delete_menu_{user_id}")
            
        builder.adjust(2)
        await callback.message.edit_reply_markup(reply_markup=builder.as_markup())

@router.message(F.text.regexp(r'(?i)^/предложить альянс'))
async def propose_alliance(message: types.Message):
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        await message.answer("⚠️ Использование: <code>/предложить альянс [тег или номер или название]</code>")
        return
        
    query = args[2].lower()
    user_id = str(message.from_user.id)
    user = get_or_create_user(user_id, message.from_user.username or message.from_user.first_name)
    clan_id = user.get('clan_id')
    if not clan_id:
        await message.answer("⚠️ Вы не состоите в клане.")
        return
        
    clan = get_db_ref(f'clans/{clan_id}').get()
    if clan.get('leader_id') != user_id:
        await message.answer("⚠️ Только лидер может предлагать альянсы.")
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
                
    if not target_clan_id:
        await message.answer("⚠️ Клан не найден.")
        return
        
    if target_clan_id == clan_id:
        await message.answer("⚠️ Вы не можете предложить альянс самому себе.")
        return
        
    allies = clan.get('allies', [])
    if target_clan_id in allies:
        await message.answer("⚠️ Вы уже в альянсе с этим кланом.")
        return
        
    target_chat_id = target_clan.get('chat_id')
    if not target_chat_id:
        await message.answer("⚠️ Клан не привязан к группе, невозможно отправить предложение.")
        return
        
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Принять", callback_data=f"ally_acc_{clan_id}_{target_clan_id}")
    builder.button(text="❌ Отклонить", callback_data=f"ally_dec_{clan_id}_{target_clan_id}")
    builder.adjust(2)
    
    try:
        await message.bot.send_message(
            target_chat_id,
            f"🤝 <b>Предложение альянса!</b>\nКлан <b>{html.escape(clan.get('name', ''))}</b> предлагает альянс клану <b>{html.escape(target_clan.get('name', ''))}</b>.",
            reply_markup=builder.as_markup()
        )
        await message.answer(f"✅ Предложение альянса отправлено клану <b>{html.escape(target_clan.get('name', ''))}</b>!")
    except Exception as e:
        await message.answer("⚠️ Не удалось отправить предложение (возможно, бот не состоит в их группе).")

@router.message(F.text.regexp(r'(?i)^/разорвать альянс'))
async def break_alliance(message: types.Message):
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        await message.answer("⚠️ Использование: <code>/разорвать альянс [тег или номер или название]</code>")
        return
        
    query = args[2].lower()
    user_id = str(message.from_user.id)
    user = get_or_create_user(user_id, message.from_user.username or message.from_user.first_name)
    clan_id = user.get('clan_id')
    if not clan_id:
        await message.answer("⚠️ Вы не состоите в клане.")
        return
        
    clan = get_db_ref(f'clans/{clan_id}').get()
    if clan.get('leader_id') != user_id:
        await message.answer("⚠️ Только лидер может разрывать альянсы.")
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
                
    if not target_clan_id:
        await message.answer("⚠️ Клан не найден.")
        return
        
    allies = clan.get('allies', [])
    if target_clan_id not in allies:
        await message.answer("⚠️ Вы не состоите в альянсе с этим кланом.")
        return
        
    allies.remove(target_clan_id)
    get_db_ref(f'clans/{clan_id}').update({'allies': allies})
    
    t_allies = target_clan.get('allies', [])
    if clan_id in t_allies:
        t_allies.remove(clan_id)
        get_db_ref(f'clans/{target_clan_id}').update({'allies': t_allies})
        
    await message.answer(f"💔 Альянс с кланом <b>{html.escape(target_clan.get('name', ''))}</b> расторгнут.")
    if target_clan.get('chat_id'):
        try:
            await message.bot.send_message(target_clan['chat_id'], f"💔 Клан <b>{html.escape(clan.get('name', ''))}</b> расторг с вами альянс.")
        except: pass

@router.message(F.text.regexp(r'(?i)^/rass'))
async def cmd_rass(message: types.Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("⚠️ Использование: <code>/rass [сообщение]</code>")
        return
        
    text = parts[1].strip()
    all_clans = get_db_ref('clans').get() or {}
    chat_ids = set(c.get('chat_id') for c in all_clans.values() if c.get('chat_id'))
    
    if not chat_ids:
        await message.answer("⚠️ Нет зарегистрированных чатов кланов для рассылки.")
        return
        
    count = 0
    for cid in chat_ids:
        try:
            await message.bot.send_message(cid, f"📢 <b>Глобальное сообщение:</b>\n\n{text}")
            count += 1
        except Exception as e:
            logging.error(f"Rass error for {cid}: {e}")
            
    await message.answer(f"✅ Разослано в {count} чатов.")

@router.message(F.text.regexp(r'(?i)^/оборона'))
async def set_defense(message: types.Message):
    args = message.text.split()
    if len(args) < 2 or not args[1].isdigit():
        await message.answer("⚠️ Использование: <code>/оборона [количество]</code>")
        return
    amount = int(args[1])
    if amount <= 0: return
    
    user_id = str(message.from_user.id)
    user = get_or_create_user(user_id, message.from_user.username or message.from_user.first_name)
    if user.get('army', 0) < amount:
        await message.answer("⚠️ У вас недостаточно солдат в резерве.")
        return
    
    new_army = user.get('army', 0) - amount
    new_def = user.get('defense_army', 0) + amount
    get_db_ref(f'users/{user_id}').update({'army': new_army, 'defense_army': new_def})
    await message.answer(f"🛡 <b>{amount}</b> солдат переведены в оборону границ и заводов.\nОни будут защищать клан с минимальными потерями.")

@router.message(F.text.regexp(r'(?i)^/столица'))
async def upgrade_capital(message: types.Message):
    args = message.text.split()
    if len(args) < 2 or not args[1].isdigit():
        await message.answer("⚠️ Использование: <code>/столица [количество монет]</code>\n(500 монет = 18 HP)")
        return
    coins = int(args[1])
    if coins < 500:
        await message.answer("⚠️ Минимальная сумма для укрепления: 500 монет.")
        return
        
    user_id = str(message.from_user.id)
    user = get_or_create_user(user_id, message.from_user.username or message.from_user.first_name)
    clan_id = user.get('clan_id')
    if not clan_id: return
    
    clan_ref = get_db_ref(f'clans/{clan_id}')
    clan = clan_ref.get()
    if clan.get('leader_id') != user_id:
        await message.answer("⚠️ Только лидер может укреплять столицу.")
        return
        
    if clan.get('gold', 0) < coins:
        await message.answer("⚠️ В казне недостаточно золота.")
        return
        
    hp_gain = (coins // 500) * 18
    spent_coins = (coins // 500) * 500
    
    clan_ref.update({'gold': clan.get('gold', 0) - spent_coins})
    await message.answer(f"🏗 <b>Начато укрепление столицы!</b>\nПотрачено: {spent_coins} золота.\nОжидаемое улучшение: +{hp_gain} HP.\n⏳ Процесс займет 10 минут...")
    
    await asyncio.sleep(600)
    
    clan = clan_ref.get()
    if clan:
        new_hp = clan.get('capital_hp', 1000) + hp_gain
        new_max = clan.get('max_capital_hp', 1000) + hp_gain
        clan_ref.update({'capital_hp': new_hp, 'max_capital_hp': new_max})
        
        chat_id = clan.get('chat_id')
        if chat_id:
            try:
                await message.bot.send_message(chat_id, f"✅ <b>Укрепление завершено!</b>\nСтолица получила +{hp_gain} HP. Текущее здоровье: {new_hp}/{new_max}")
            except: pass

@router.message()
async def handle_all(message: types.Message):
    # Ignore messages that don't start with / to avoid spam in groups
    if not message.text or not message.text.startswith('/'):
        return
    logging.info(f"Received unhandled command: {message.text}")
    # await message.answer("Я не понимаю эту команду. Используйте /boevik для списка команд.")
