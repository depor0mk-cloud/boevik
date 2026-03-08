import logging
from datetime import datetime, timedelta
from aiogram import Router, types, F
from aiogram.filters import Command
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

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    text = (
        "⚔️ <b>Добро пожаловать в Клан-Бот!</b> ⚔️\n\n"
        "<b>Управление кланом:</b>\n"
        "!создать_клан [название] [тег] — создать клан\n"
        "!вступить [название/тег] — вступить в клан\n"
        "!выйти — покинуть клан\n"
        "!мой_клан — инфо о клане\n\n"
        "<b>Война:</b>\n"
        "!объявить_войну [клан] — начать войну\n"
        "!белый_мир — предложить мир\n"
        "!капитуляция — сдаться\n"
        "!аннексия — захват территории\n\n"
        "<b>Экономика и прокачка:</b>\n"
        "!мобилизация [1-100] — отправить армию (КД 12ч)\n"
        "!тренировка [сила/защита/здоровье] — прокачка (КД 24ч)\n"
        "!строй_завод [оружейный/финансовый/оборонительный] — постройка (КД 48ч)"
    )
    await message.answer(text)

@router.message(Command("создать_клан", prefix="!/"))
async def create_clan(message: types.Message):
    args = message.text.split()
    if len(args) < 3:
        await message.answer("Использование: !создать_клан [название] [тег]")
        return
    tag = args[-1]
    name = " ".join(args[1:-1])
    user_id = str(message.from_user.id)
    username = message.from_user.username or user_id
    
    user = get_or_create_user(user_id, username)
    if user.get('clan_id'):
        await message.answer("Вы уже состоите в клане!")
        return
        
    clans_ref = get_db_ref('clans')
    all_clans = clans_ref.get() or {}
    for cid, cdata in all_clans.items():
        if cdata.get('name') == name or cdata.get('tag') == tag:
            await message.answer("Клан с таким названием или тегом уже существует.")
            return
            
    new_clan_data = {
        'name': name,
        'tag': tag,
        'leader_id': user_id,
        'exp': 0,
        'capital_hp': 1000,
        'max_capital_hp': 1000,
        'population_limit': 10,
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
    await message.answer(f"Клан <b>{name}</b> [{tag}] успешно создан! Вы стали лидером.")

@router.message(Command("вступить", prefix="!/"))
async def join_clan(message: types.Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Использование: !вступить [название или тег]")
        return
    query = args[1]
    user_id = str(message.from_user.id)
    username = message.from_user.username or user_id
    
    user = get_or_create_user(user_id, username)
    if user.get('clan_id'):
        await message.answer("Вы уже состоите в клане! Сначала покиньте его (!выйти).")
        return
        
    all_clans = get_db_ref('clans').get() or {}
    target_clan_id = None
    target_clan = None
    for cid, cdata in all_clans.items():
        if cdata.get('name') == query or cdata.get('tag') == query:
            target_clan_id = cid
            target_clan = cdata
            break
            
    if not target_clan:
        await message.answer("Клан не найден.")
        return
        
    all_users = get_db_ref('users').get() or {}
    members_count = sum(1 for u in all_users.values() if u.get('clan_id') == target_clan_id)
    
    if members_count >= target_clan.get('population_limit', 10):
        await message.answer("В клане нет мест! Лидер должен построить больше заводов.")
        return
        
    get_db_ref(f'users/{user_id}').update({'clan_id': target_clan_id})
    await message.answer(f"Вы успешно вступили в клан <b>{target_clan['name']}</b>!")

@router.message(Command("выйти", prefix="!/"))
async def leave_clan(message: types.Message):
    user_id = str(message.from_user.id)
    user = get_or_create_user(user_id, message.from_user.username)
    clan_id = user.get('clan_id')
    
    if not clan_id:
        await message.answer("Вы не состоите в клане.")
        return
        
    clan = get_db_ref(f'clans/{clan_id}').get()
    if clan and clan.get('leader_id') == user_id:
        await message.answer("Вы лидер клана! Передайте лидерство или распустите клан (функция в разработке).")
        return
        
    get_db_ref(f'users/{user_id}').update({'clan_id': None, 'army': 0})
    await message.answer("Вы покинули клан.")

@router.message(Command("мой_клан", prefix="!/"))
async def my_clan(message: types.Message):
    user_id = str(message.from_user.id)
    user = get_or_create_user(user_id, message.from_user.username)
    clan_id = user.get('clan_id')
    
    if not clan_id:
        await message.answer("Вы не состоите в клане.")
        return
        
    clan = get_db_ref(f'clans/{clan_id}').get()
    if not clan:
        await message.answer("Ваш клан не найден (возможно, был удален).")
        get_db_ref(f'users/{user_id}').update({'clan_id': None})
        return
        
    all_users = get_db_ref('users').get() or {}
    clan_users = [u for u in all_users.values() if u.get('clan_id') == clan_id]
    members_count = len(clan_users)
    total_army = sum(u.get('army', 0) for u in clan_users)
    
    war_status = "Мир"
    if clan.get('war_id'):
        war_status = "В состоянии войны ⚔️"
        
    text = (
        f"🛡 <b>Клан:</b> {clan.get('name')} [{clan.get('tag')}]\n"
        f"👑 <b>Лидер:</b> <a href='tg://user?id={clan.get('leader_id')}'>Лидер</a>\n"
        f"👥 <b>Участники:</b> {members_count} / {clan.get('population_limit', 10)}\n"
        f"⚔️ <b>Армия клана:</b> {total_army}\n"
        f"🏰 <b>Столица:</b> {clan.get('capital_hp', 1000)} / {clan.get('max_capital_hp', 1000)} HP\n"
        f"💰 <b>Золото:</b> {clan.get('gold', 0)}\n"
        f"🌟 <b>Опыт:</b> {clan.get('exp', 0)}\n"
        f"📊 <b>Статус:</b> {war_status}\n\n"
        f"<b>Уровни:</b>\n"
        f"💪 Сила: {clan.get('power_level', 1)} | 🛡 Защита: {clan.get('defense_level', 1)} | ❤️ Здоровье: {clan.get('health_level', 1)}\n\n"
        f"<b>Заводы:</b>\n"
        f"🔫 Оружейные: {clan.get('factory_weapon', 0)} | 🏦 Финансовые: {clan.get('factory_finance', 0)} | 🧱 Оборонительные: {clan.get('factory_defense', 0)}"
    )
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
        
    user_id = str(message.from_user.id)
    user = get_or_create_user(user_id, message.from_user.username)
    if not user.get('clan_id'):
        await message.answer("Вы не состоите в клане.")
        return
        
    now = datetime.now()
    if user.get('last_mobilization'):
        last_mob = datetime.fromisoformat(user['last_mobilization'])
        if now - last_mob < timedelta(hours=12):
            rem = timedelta(hours=12) - (now - last_mob)
            await message.answer(f"КД на мобилизацию! Осталось: {rem.seconds//3600}ч {(rem.seconds//60)%60}м")
            return
            
    new_army = user.get('army', 0) + amount
    get_db_ref(f'users/{user_id}').update({
        'army': new_army,
        'last_mobilization': now.isoformat()
    })
    await message.answer(f"Вы успешно мобилизовали {amount} солдат в армию клана! ⚔️")

@router.message(Command("тренировка", prefix="!/"))
async def train(message: types.Message):
    args = message.text.split()
    if len(args) < 2 or args[1].lower() not in ['сила', 'защита', 'здоровье']:
        await message.answer("Использование: !тренировка [сила/защита/здоровье]")
        return
    stat = args[1].lower()
    
    user_id = str(message.from_user.id)
    user = get_or_create_user(user_id, message.from_user.username)
    clan_id = user.get('clan_id')
    if not clan_id:
        await message.answer("Вы не состоите в клане.")
        return
        
    now = datetime.now()
    if user.get('last_train'):
        last_train = datetime.fromisoformat(user['last_train'])
        if now - last_train < timedelta(hours=24):
            rem = timedelta(hours=24) - (now - last_train)
            await message.answer(f"КД на тренировку! Осталось: {rem.seconds//3600}ч {(rem.seconds//60)%60}м")
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
    
    await message.answer(f"Вы успешно потренировали клан! Навык '{stat}' повышен до {new_level}. 💪")

@router.message(Command("строй_завод", prefix="!/"))
async def build_factory(message: types.Message):
    args = message.text.split()
    valid_types = ['оружейный', 'финансовый', 'оборонительный']
    if len(args) < 2 or args[1].lower() not in valid_types:
        await message.answer("Использование: !строй_завод [оружейный/финансовый/оборонительный]")
        return
    ftype = args[1].lower()
    
    user_id = str(message.from_user.id)
    user = get_or_create_user(user_id, message.from_user.username)
    clan_id = user.get('clan_id')
    if not clan_id:
        await message.answer("Вы не состоите в клане.")
        return
        
    now = datetime.now()
    if user.get('last_factory'):
        last_fac = datetime.fromisoformat(user['last_factory'])
        if now - last_fac < timedelta(hours=48):
            rem = timedelta(hours=48) - (now - last_fac)
            await message.answer(f"КД на постройку! Осталось: {rem.days}д {rem.seconds//3600}ч")
            return
            
    field = ""
    if ftype == 'оружейный': field = 'factory_weapon'
    elif ftype == 'финансовый': field = 'factory_finance'
    elif ftype == 'оборонительный': field = 'factory_defense'
    
    clan_ref = get_db_ref(f'clans/{clan_id}')
    clan = clan_ref.get()
    
    new_factory_count = clan.get(field, 0) + 1
    new_pop_limit = clan.get('population_limit', 10) + 1
    
    clan_ref.update({
        field: new_factory_count,
        'population_limit': new_pop_limit
    })
    get_db_ref(f'users/{user_id}').update({'last_factory': now.isoformat()})
    
    await message.answer(f"Вы успешно построили {ftype} завод! Лимит населения увеличен на 1. 🏭")

@router.message(Command("объявить_войну", prefix="!/"))
async def declare_war(message: types.Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Использование: !объявить_войну [название или тег клана]")
        return
    target_query = args[1]
    
    user_id = str(message.from_user.id)
    user = get_or_create_user(user_id, message.from_user.username)
    attacker_id = user.get('clan_id')
    
    if not attacker_id:
        await message.answer("Вы не состоите в клане.")
        return
        
    attacker = get_db_ref(f'clans/{attacker_id}').get()
    if attacker.get('leader_id') != user_id:
        await message.answer("Только лидер может объявлять войну!")
        return
        
    if attacker.get('war_id'):
        await message.answer("Ваш клан уже участвует в войне!")
        return
        
    all_clans = get_db_ref('clans').get() or {}
    defender_id = None
    defender = None
    for cid, cdata in all_clans.items():
        if cdata.get('name') == target_query or cdata.get('tag') == target_query:
            defender_id = cid
            defender = cdata
            break
            
    if not defender:
        await message.answer("Клан противника не найден.")
        return
        
    if defender_id == attacker_id:
        await message.answer("Нельзя объявить войну самому себе.")
        return
        
    if defender.get('war_id'):
        await message.answer("Этот клан уже с кем-то воюет.")
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
    
    await message.answer(f"⚔️ Клан <b>{attacker['name']}</b> объявил войну клану <b>{defender['name']}</b>!\nГотовьтесь к битвам!")

@router.message(Command("белый_мир", prefix="!/"))
async def white_peace(message: types.Message):
    user_id = str(message.from_user.id)
    user = get_or_create_user(user_id, message.from_user.username)
    clan_id = user.get('clan_id')
    if not clan_id: return
    
    clan = get_db_ref(f'clans/{clan_id}').get()
    if clan.get('leader_id') != user_id:
        await message.answer("Только лидер может предлагать мир.")
        return
        
    war_id = clan.get('war_id')
    if not war_id:
        await message.answer("Ваш клан не воюет.")
        return
        
    war_ref = get_db_ref(f'wars/{war_id}')
    war = war_ref.get()
    if not war: return
    
    if war.get('white_peace_offer') == clan_id:
        await message.answer("Вы уже предложили белый мир. Ожидайте ответа.")
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
        await message.answer("🕊 Вы предложили белый мир. Чтобы он вступил в силу, лидер вражеского клана должен также написать !белый_мир.")

@router.message(Command("капитуляция", prefix="!/"))
async def capitulate(message: types.Message):
    user_id = str(message.from_user.id)
    user = get_or_create_user(user_id, message.from_user.username)
    clan_id = user.get('clan_id')
    if not clan_id: return
    
    clan = get_db_ref(f'clans/{clan_id}').get()
    if clan.get('leader_id') != user_id:
        await message.answer("Только лидер может капитулировать.")
        return
        
    war_id = clan.get('war_id')
    if not war_id:
        await message.answer("Ваш клан не воюет.")
        return
        
    if clan.get('capital_hp', 1000) > 0:
        await message.answer("Капитуляция доступна только если здоровье вашей столицы равно 0!")
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

@router.message(Command("аннексия", prefix="!/"))
async def annex(message: types.Message):
    user_id = str(message.from_user.id)
    user = get_or_create_user(user_id, message.from_user.username)
    clan_id = user.get('clan_id')
    if not clan_id: return
    
    clan = get_db_ref(f'clans/{clan_id}').get()
    if clan.get('leader_id') != user_id:
        await message.answer("Только лидер может проводить аннексию.")
        return
        
    war_id = clan.get('war_id')
    if not war_id:
        await message.answer("Ваш клан не воюет.")
        return
        
    war_ref = get_db_ref(f'wars/{war_id}')
    war = war_ref.get()
    if not war: return
    
    loser_id = war['defender_id'] if war['attacker_id'] == clan_id else war['attacker_id']
    loser = get_db_ref(f'clans/{loser_id}').get()
    
    if loser.get('capital_hp', 1000) > loser.get('max_capital_hp', 1000) * 0.2:
        await message.answer("Аннексия доступна только если здоровье вражеской столицы ниже 20%!")
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
        'population_limit': clan.get('population_limit', 10) + 1
    })
    
    # Transfer some users
    all_users = get_db_ref('users').get() or {}
    loser_users = [uid for uid, u in all_users.items() if u.get('clan_id') == loser_id]
    transfer_count = int(len(loser_users) * 0.3)
    
    for i in range(transfer_count):
        get_db_ref(f'users/{loser_users[i]}').update({'clan_id': clan_id})
        
    war_ref.delete()
    await message.answer(f"⚔️ Вы успешно аннексировали часть территории клана <b>{loser.get('name')}</b>! Получено золото и новые участники.")

@router.message()
async def handle_all(message: types.Message):
    logging.info(f"Received unhandled message: {message.text}")
    await message.answer("Я не понимаю эту команду. Проверьте список доступных команд.")
