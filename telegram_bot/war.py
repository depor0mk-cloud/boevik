import asyncio
import logging
from datetime import datetime, timedelta
from db import get_conn
from config import WAR_TICK_HOURS

async def war_tick_loop(bot):
    while True:
        try:
            await process_wars(bot)
        except Exception as e:
            logging.error(f"Error in war tick: {e}")
        await asyncio.sleep(60) # Check every minute if a tick is due

async def process_wars(bot):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM wars")
    wars = c.fetchall()
    
    now = datetime.now()
    
    for war in wars:
        last_tick = datetime.fromisoformat(war['last_tick'])
        if now - last_tick >= timedelta(hours=WAR_TICK_HOURS):
            # Process tick
            c.execute("SELECT * FROM clans WHERE id = ?", (war['attacker_id'],))
            attacker = c.fetchone()
            c.execute("SELECT * FROM clans WHERE id = ?", (war['defender_id'],))
            defender = c.fetchone()
            
            c.execute("SELECT SUM(army) as total FROM users WHERE clan_id = ?", (attacker['id'],))
            att_army = c.fetchone()['total'] or 0
            
            c.execute("SELECT SUM(army) as total FROM users WHERE clan_id = ?", (defender['id'],))
            def_army = c.fetchone()['total'] or 0
            
            att_power = att_army * attacker['power_level'] * (1 + 0.05 * attacker['factory_weapon'])
            def_power = def_army * defender['defense_level'] * (1 + 0.05 * defender['factory_defense'])
            
            damage = int(att_power - def_power)
            
            msg = ""
            if damage > 0:
                # Defender takes damage
                new_hp = max(0, defender['capital_hp'] - damage)
                c.execute("UPDATE clans SET capital_hp = ? WHERE id = ?", (new_hp, defender['id']))
                msg = f"🔥 Клан <b>{attacker['name']}</b> прорвал оборону! Столица <b>{defender['name']}</b> получила {damage} урона. (Осталось: {new_hp} HP)"
            elif damage < 0:
                # Attacker takes damage
                new_hp = max(0, attacker['capital_hp'] - abs(damage))
                c.execute("UPDATE clans SET capital_hp = ? WHERE id = ?", (new_hp, attacker['id']))
                msg = f"🛡️ Клан <b>{defender['name']}</b> отразил атаку! Столица <b>{attacker['name']}</b> получила {abs(damage)} урона. (Осталось: {new_hp} HP)"
            else:
                msg = f"⚔️ Битва между <b>{attacker['name']}</b> и <b>{defender['name']}</b> завершилась вничью. Никто не получил урона."
                
            c.execute("UPDATE wars SET last_tick = ? WHERE id = ?", (now.isoformat(), war['id']))
            conn.commit()
            
            # Here we would send message to the global chat if we had its ID.
            # For now, we just log it. In a real bot, we'd broadcast to a specific channel or to leaders.
            logging.info(msg)
            
    conn.close()
