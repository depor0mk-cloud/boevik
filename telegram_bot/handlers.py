import sqlite3
import logging
from datetime import datetime, timedelta
from aiogram import Router, types, F
from aiogram.filters import Command
from db import get_conn

router = Router()

def get_or_create_user(user_id, username):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = c.fetchone()
    if not user:
        c.execute("INSERT INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
        conn.commit()
        c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = c.fetchone()
    conn.close()
    return user

@router.message(Command("создать_клан", prefix="!/"))
async def create_clan(message: types.Message):
    args = message.text.split()
    if len(args) < 3:
        await message.answer("Использование: !создать_клан [название] [тег]")
        return
    tag = args[-1]
    name = " ".join(args[1:-1])
    user_id = message.from_user.id
    username = message.from_user.username or str(user_id)
    
    user = get_or_create_user(user_id, username)
    if user['clan_id']:
        await message.answer("Вы уже состоите в клане!")
        return
        
    conn = get_conn()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO clans (name, tag, leader_id) VALUES (?, ?, ?)", (name, tag, user_id))
        clan_id = c.lastrowid
        c.execute("UPDATE users SET clan_id = ? WHERE user_id = ?", (clan_id, user_id))
        conn.commit()
        await message.answer(f"Клан <b>{name}</b> [{tag}] успешно создан! Вы стали лидером.")
    except sqlite3.IntegrityError:
        await message.answer("Клан с таким названием или тегом уже существует.")
    finally:
        conn.close()

@router.message(Command("вступить", prefix="!/"))
async def join_clan(message: types.Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Использование: !вступить [название или тег]")
        return
    query = args[1]
    user_id = message.from_user.id
    username = message.from_user.username or str(user_id)
    
    user = get_or_create_user(user_id, username)
    if user['clan_id']:
        await message.answer("Вы уже состоите в клане! Сначала покиньте его (!выйти).")
        return
        
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM clans WHERE name = ? OR tag = ?", (query, query))
    clan = c.fetchone()
    if not clan:
        await message.answer("Клан не найден.")
        conn.close()
        return
        
    c.execute("SELECT COUNT(*) as cnt FROM users WHERE clan_id = ?", (clan['id'],))
    members_count = c.fetchone()['cnt']
    if members_count >= clan['population_limit']:
        await message.answer("В клане нет мест! Лидер должен построить больше заводов.")
        conn.close()
        return
        
    c.execute("UPDATE users SET clan_id = ? WHERE user_id = ?", (clan['id'], user_id))
    conn.commit()
    conn.close()
    await message.answer(f"Вы успешно вступили в клан <b>{clan['name']}</b>!")

@router.message(Command("выйти", prefix="!/"))
async def leave_clan(message: types.Message):
    user_id = message.from_user.id
    user = get_or_create_user(user_id, message.from_user.username)
    if not user['clan_id']:
        await message.answer("Вы не состоите в клане.")
        return
        
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM clans WHERE id = ?", (user['clan_id'],))
    clan = c.fetchone()
    
    if clan['leader_id'] == user_id:
        await message.answer("Вы лидер клана! Передайте лидерство или распустите клан (функция в разработке).")
        conn.close()
        return
        
    c.execute("UPDATE users SET clan_id = NULL, army = 0 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    await message.answer("Вы покинули клан.")

@router.message(Command("мой_клан", prefix="!/"))
async def my_clan(message: types.Message):
    user_id = message.from_user.id
    user = get_or_create_user(user_id, message.from_user.username)
    if not user['clan_id']:
        await message.answer("Вы не состоите в клане.")
        return
        
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM clans WHERE id = ?", (user['clan_id'],))
    clan = c.fetchone()
    
    c.execute("SELECT COUNT(*) as cnt, SUM(army) as total_army FROM users WHERE clan_id = ?", (clan['id'],))
    stats = c.fetchone()
    members_count = stats['cnt']
    total_army = stats['total_army'] or 0
    
    war_status = "Мир"
    if clan['war_id']:
        war_status = "В состоянии войны ⚔️"
        
    text = (
        f"🛡 <b>Клан:</b> {clan['name']} [{clan['tag']}]\n"
        f"👑 <b>Лидер:</b> <a href='tg://user?id={clan['leader_id']}'>Лидер</a>\n"
        f"👥 <b>Участники:</b> {members_count} / {clan['population_limit']}\n"
        f"⚔️ <b>Армия клана:</b> {total_army}\n"
        f"🏰 <b>Столица:</b> {clan['capital_hp']} / {clan['max_capital_hp']} HP\n"
        f"💰 <b>Золото:</b> {clan['gold']}\n"
        f"🌟 <b>Опыт:</b> {clan['exp']}\n"
        f"📊 <b>Статус:</b> {war_status}\n\n"
        f"<b>Уровни:</b>\n"
        f"💪 Сила: {clan['power_level']} | 🛡 Защита: {clan['defense_level']} | ❤️ Здоровье: {clan['health_level']}\n\n"
        f"<b>Заводы:</b>\n"
        f"🔫 Оружейные: {clan['factory_weapon']} | 🏦 Финансовые: {clan['factory_finance']} | 🧱 Оборонительные: {clan['factory_defense']}"
    )
    conn.close()
    await message.answer(text)

@router.message(Command("мобилизация", prefix="!/"))
async def mobilize(message: types.Message):
    args = message.text.split()
    if len(args) < 2 or not args[1].isdigit():
        await message.answer("Использование: !мобилизация [количество от 1 до 100]")
        return
    amount = int(args[1])
    if not (1 <= amount <= 100):
        await message.answer("Количество должно быть от 1 до 100.")
        return
        
    user_id = message.from_user.id
    user = get_or_create_user(user_id, message.from_user.username)
    if not user['clan_id']:
        await message.answer("Вы не состоите в клане.")
        return
        
    now = datetime.now()
    if user['last_mobilization']:
        last_mob = datetime.fromisoformat(user['last_mobilization'])
        if now - last_mob < timedelta(hours=12):
            rem = timedelta(hours=12) - (now - last_mob)
            await message.answer(f"КД на мобилизацию! Осталось: {rem.seconds//3600}ч {(rem.seconds//60)%60}м")
            return
            
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE users SET army = army + ?, last_mobilization = ? WHERE user_id = ?", (amount, now.isoformat(), user_id))
    conn.commit()
    conn.close()
    await message.answer(f"Вы успешно мобилизовали {amount} солдат в армию клана! ⚔️")

@router.message(Command("тренировка", prefix="!/"))
async def train(message: types.Message):
    args = message.text.split()
    if len(args) < 2 or args[1].lower() not in ['сила', 'защита', 'здоровье']:
        await message.answer("Использование: !тренировка [сила/защита/здоровье]")
        return
    stat = args[1].lower()
    
    user_id = message.from_user.id
    user = get_or_create_user(user_id, message.from_user.username)
    if not user['clan_id']:
        await message.answer("Вы не состоите в клане.")
        return
        
    now = datetime.now()
    if user['last_train']:
        last_train = datetime.fromisoformat(user['last_train'])
        if now - last_train < timedelta(hours=24):
            rem = timedelta(hours=24) - (now - last_train)
            await message.answer(f"КД на тренировку! Осталось: {rem.seconds//3600}ч {(rem.seconds//60)%60}м")
            return
            
    conn = get_conn()
    c = conn.cursor()
    
    field = ""
    if stat == 'сила': field = 'power_level'
    elif stat == 'защита': field = 'defense_level'
    elif stat == 'здоровье': field = 'health_level'
    
    c.execute(f"UPDATE clans SET {field} = {field} + 1 WHERE id = ?", (user['clan_id'],))
    c.execute("UPDATE users SET last_train = ? WHERE user_id = ?", (now.isoformat(), user_id))
    conn.commit()
    conn.close()
    await message.answer(f"Вы успешно потренировали клан! Навык '{stat}' повышен. 💪")

@router.message(Command("строй_завод", prefix="!/"))
async def build_factory(message: types.Message):
    args = message.text.split()
    valid_types = ['оружейный', 'финансовый', 'оборонительный']
    if len(args) < 2 or args[1].lower() not in valid_types:
        await message.answer("Использование: !строй_завод [оружейный/финансовый/оборонительный]")
        return
    ftype = args[1].lower()
    
    user_id = message.from_user.id
    user = get_or_create_user(user_id, message.from_user.username)
    if not user['clan_id']:
        await message.answer("Вы не состоите в клане.")
        return
        
    now = datetime.now()
    if user['last_factory']:
        last_fac = datetime.fromisoformat(user['last_factory'])
        if now - last_fac < timedelta(hours=48):
            rem = timedelta(hours=48) - (now - last_fac)
            await message.answer(f"КД на постройку! Осталось: {rem.days}д {rem.seconds//3600}ч")
            return
            
    conn = get_conn()
    c = conn.cursor()
    
    field = ""
    if ftype == 'оружейный': field = 'factory_weapon'
    elif ftype == 'финансовый': field = 'factory_finance'
    elif ftype == 'оборонительный': field = 'factory_defense'
    
    c.execute(f"UPDATE clans SET {field} = {field} + 1, population_limit = population_limit + 1 WHERE id = ?", (user['clan_id'],))
    c.execute("UPDATE users SET last_factory = ? WHERE user_id = ?", (now.isoformat(), user_id))
    conn.commit()
    conn.close()
    await message.answer(f"Вы успешно построили {ftype} завод! Лимит населения увеличен на 1. 🏭")

@router.message(Command("объявить_войну", prefix="!/"))
async def declare_war(message: types.Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Использование: !объявить_войну [название или тег клана]")
        return
    target_query = args[1]
    
    user_id = message.from_user.id
    user = get_or_create_user(user_id, message.from_user.username)
    if not user['clan_id']:
        await message.answer("Вы не состоите в клане.")
        return
        
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM clans WHERE id = ?", (user['clan_id'],))
    attacker = c.fetchone()
    
    if attacker['leader_id'] != user_id:
        await message.answer("Только лидер может объявлять войну!")
        conn.close()
        return
        
    if attacker['war_id']:
        await message.answer("Ваш клан уже участвует в войне!")
        conn.close()
        return
        
    c.execute("SELECT * FROM clans WHERE name = ? OR tag = ?", (target_query, target_query))
    defender = c.fetchone()
    
    if not defender:
        await message.answer("Клан противника не найден.")
        conn.close()
        return
        
    if defender['id'] == attacker['id']:
        await message.answer("Нельзя объявить войну самому себе.")
        conn.close()
        return
        
    if defender['war_id']:
        await message.answer("Этот клан уже с кем-то воюет.")
        conn.close()
        return
        
    now = datetime.now().isoformat()
    c.execute("INSERT INTO wars (attacker_id, defender_id, start_time, last_tick) VALUES (?, ?, ?, ?)", 
              (attacker['id'], defender['id'], now, now))
    war_id = c.lastrowid
    
    c.execute("UPDATE clans SET war_id = ? WHERE id IN (?, ?)", (war_id, attacker['id'], defender['id']))
    conn.commit()
    conn.close()
    
    await message.answer(f"⚔️ Клан <b>{attacker['name']}</b> объявил войну клану <b>{defender['name']}</b>!\nГотовьтесь к битвам!")

@router.message(Command("белый_мир", prefix="!/"))
async def white_peace(message: types.Message):
    user_id = message.from_user.id
    user = get_or_create_user(user_id, message.from_user.username)
    if not user['clan_id']: return
    
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM clans WHERE id = ?", (user['clan_id'],))
    clan = c.fetchone()
    
    if clan['leader_id'] != user_id:
        await message.answer("Только лидер может предлагать мир.")
        conn.close()
        return
        
    if not clan['war_id']:
        await message.answer("Ваш клан не воюет.")
        conn.close()
        return
        
    c.execute("SELECT * FROM wars WHERE id = ?", (clan['war_id'],))
    war = c.fetchone()
    
    if war['white_peace_offer'] == clan['id']:
        await message.answer("Вы уже предложили белый мир. Ожидайте ответа.")
        conn.close()
        return
        
    if war['white_peace_offer'] and war['white_peace_offer'] != clan['id']:
        # Accept peace
        c.execute("UPDATE clans SET war_id = NULL, exp = MAX(0, exp - (exp * 15 / 100)) WHERE id IN (?, ?)", (war['attacker_id'], war['defender_id']))
        c.execute("DELETE FROM wars WHERE id = ?", (war['id'],))
        conn.commit()
        await message.answer("🤝 Белый мир заключён! Оба клана потеряли 15% опыта.")
    else:
        # Offer peace
        c.execute("UPDATE wars SET white_peace_offer = ? WHERE id = ?", (clan['id'], war['id']))
        conn.commit()
        await message.answer("🕊 Вы предложили белый мир. Чтобы он вступил в силу, лидер вражеского клана должен также написать !белый_мир.")
    conn.close()

@router.message(Command("капитуляция", prefix="!/"))
async def capitulate(message: types.Message):
    user_id = message.from_user.id
    user = get_or_create_user(user_id, message.from_user.username)
    if not user['clan_id']: return
    
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM clans WHERE id = ?", (user['clan_id'],))
    clan = c.fetchone()
    
    if clan['leader_id'] != user_id:
        await message.answer("Только лидер может капитулировать.")
        conn.close()
        return
        
    if not clan['war_id']:
        await message.answer("Ваш клан не воюет.")
        conn.close()
        return
        
    if clan['capital_hp'] > 0:
        await message.answer("Капитуляция доступна только если здоровье вашей столицы равно 0!")
        conn.close()
        return
        
    c.execute("SELECT * FROM wars WHERE id = ?", (clan['war_id'],))
    war = c.fetchone()
    
    winner_id = war['attacker_id'] if war['defender_id'] == clan['id'] else war['defender_id']
    
    # Apply capitulation effects
    c.execute("UPDATE clans SET exp = MAX(0, exp - (exp * 50 / 100)), factory_weapon = MAX(0, factory_weapon - 1), factory_finance = MAX(0, factory_finance - 1), war_id = NULL, capital_hp = max_capital_hp WHERE id = ?", (clan['id'],))
    
    # Winner gets resources
    c.execute("SELECT gold FROM clans WHERE id = ?", (clan['id'],))
    loser_gold = c.fetchone()['gold']
    stolen_gold = int(loser_gold * 0.3)
    
    c.execute("UPDATE clans SET gold = gold - ? WHERE id = ?", (stolen_gold, clan['id']))
    c.execute("UPDATE clans SET gold = gold + ?, war_id = NULL WHERE id = ?", (stolen_gold, winner_id))
    
    c.execute("DELETE FROM wars WHERE id = ?", (war['id'],))
    conn.commit()
    conn.close()
    
    await message.answer(f"🏳️ Ваш клан капитулировал! Вы потеряли 50% опыта, часть заводов и {stolen_gold} золота.")

@router.message(Command("аннексия", prefix="!/"))
async def annex(message: types.Message):
    user_id = message.from_user.id
    user = get_or_create_user(user_id, message.from_user.username)
    if not user['clan_id']: return
    
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM clans WHERE id = ?", (user['clan_id'],))
    clan = c.fetchone()
    
    if clan['leader_id'] != user_id:
        await message.answer("Только лидер может проводить аннексию.")
        conn.close()
        return
        
    if not clan['war_id']:
        await message.answer("Ваш клан не воюет.")
        conn.close()
        return
        
    c.execute("SELECT * FROM wars WHERE id = ?", (clan['war_id'],))
    war = c.fetchone()
    
    loser_id = war['defender_id'] if war['attacker_id'] == clan['id'] else war['attacker_id']
    c.execute("SELECT * FROM clans WHERE id = ?", (loser_id,))
    loser = c.fetchone()
    
    if loser['capital_hp'] > loser['max_capital_hp'] * 0.2:
        await message.answer("Аннексия доступна только если здоровье вражеской столицы ниже 20%!")
        conn.close()
        return
        
    # Apply annexation effects
    c.execute("UPDATE clans SET exp = MAX(0, exp - (exp * 25 / 100)), capital_hp = max_capital_hp / 2, war_id = NULL WHERE id = ?", (loser['id'],))
    
    stolen_gold = int(loser['gold'] * 0.2)
    c.execute("UPDATE clans SET gold = gold - ? WHERE id = ?", (stolen_gold, loser['id']))
    c.execute("UPDATE clans SET gold = gold + ?, war_id = NULL, population_limit = population_limit + 1 WHERE id = ?", (stolen_gold, clan['id']))
    
    # Transfer some users
    c.execute("SELECT user_id FROM users WHERE clan_id = ?", (loser['id'],))
    loser_users = c.fetchall()
    transfer_count = int(len(loser_users) * 0.3)
    for i in range(transfer_count):
        c.execute("UPDATE users SET clan_id = ? WHERE user_id = ?", (clan['id'], loser_users[i]['user_id']))
        
    c.execute("DELETE FROM wars WHERE id = ?", (war['id'],))
    conn.commit()
    conn.close()
    
    await message.answer(f"⚔️ Вы успешно аннексировали часть территории клана <b>{loser['name']}</b>! Получено золото и новые участники.")

@router.message()
async def handle_all(message: types.Message):
    logging.info(f"Received unhandled message: {message.text}")
    await message.answer("Я не понимаю эту команду. Проверьте список доступных команд.")
