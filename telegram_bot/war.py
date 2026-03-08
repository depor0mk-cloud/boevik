import asyncio
import logging
import html
from datetime import datetime, timedelta
from firebase_db import get_db_ref
from config import WAR_TICK_HOURS

async def war_tick_loop(bot):
    while True:
        try:
            await process_wars(bot)
        except Exception as e:
            logging.error(f"Error in war tick: {e}")
        await asyncio.sleep(60) # Check every minute if a tick is due

async def process_wars(bot):
    wars_ref = get_db_ref('wars')
    wars = wars_ref.get() or {}
    
    now = datetime.now()
    
    for war_id, war in wars.items():
        last_tick_str = war.get('last_tick')
        if not last_tick_str: continue
        last_tick = datetime.fromisoformat(last_tick_str)
        
        if now - last_tick >= timedelta(hours=WAR_TICK_HOURS):
            attacker_id = war['attacker_id']
            defender_id = war['defender_id']
            
            attacker = get_db_ref(f'clans/{attacker_id}').get()
            defender = get_db_ref(f'clans/{defender_id}').get()
            
            if not attacker or not defender:
                continue
                
            all_users = get_db_ref('users').get() or {}
            att_army = sum(u.get('army', 0) for u in all_users.values() if u.get('clan_id') == attacker_id)
            def_army = sum(u.get('army', 0) for u in all_users.values() if u.get('clan_id') == defender_id)
            
            att_power = att_army * attacker.get('power_level', 1) * (1 + 0.05 * attacker.get('factory_weapon', 0))
            def_power = def_army * defender.get('defense_level', 1) * (1 + 0.05 * defender.get('factory_defense', 0))
            
            damage = int(att_power - def_power)
            
            msg = ""
            if damage > 0:
                # Defender takes damage
                new_hp = max(0, defender.get('capital_hp', 1000) - damage)
                get_db_ref(f'clans/{defender_id}').update({'capital_hp': new_hp})
                msg = f"🔥 Клан <b>{html.escape(attacker['name'])}</b> прорвал оборону! Столица <b>{html.escape(defender['name'])}</b> получила {damage} урона. (Осталось: {new_hp} HP)"
            elif damage < 0:
                # Attacker takes damage
                new_hp = max(0, attacker.get('capital_hp', 1000) - abs(damage))
                get_db_ref(f'clans/{attacker_id}').update({'capital_hp': new_hp})
                msg = f"🛡️ Клан <b>{html.escape(defender['name'])}</b> отразил атаку! Столица <b>{html.escape(attacker['name'])}</b> получила {abs(damage)} урона. (Осталось: {new_hp} HP)"
            else:
                msg = f"⚔️ Битва между <b>{html.escape(attacker['name'])}</b> и <b>{html.escape(defender['name'])}</b> завершилась вничью. Никто не получил урона."
                
            get_db_ref(f'wars/{war_id}').update({'last_tick': now.isoformat()})
            
            # Send notification to both clans if they have a registered chat_id
            if msg:
                for cid in [attacker_id, defender_id]:
                    c_data = attacker if cid == attacker_id else defender
                    chat_id = c_data.get('chat_id')
                    if chat_id:
                        try:
                            await bot.send_message(chat_id, msg)
                        except Exception as e:
                            logging.error(f"Failed to send message to {chat_id}: {e}")
            
            logging.info(msg)
