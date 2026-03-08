import sqlite3
from datetime import datetime

DB_PATH = 'clans.db'

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS clans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        tag TEXT UNIQUE,
        leader_id INTEGER,
        exp INTEGER DEFAULT 0,
        capital_hp INTEGER DEFAULT 1000,
        max_capital_hp INTEGER DEFAULT 1000,
        population_limit INTEGER DEFAULT 10,
        gold INTEGER DEFAULT 0,
        power_level INTEGER DEFAULT 1,
        defense_level INTEGER DEFAULT 1,
        health_level INTEGER DEFAULT 1,
        factory_weapon INTEGER DEFAULT 0,
        factory_finance INTEGER DEFAULT 0,
        factory_defense INTEGER DEFAULT 0,
        war_id INTEGER DEFAULT NULL
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        clan_id INTEGER,
        army INTEGER DEFAULT 0,
        last_mobilization TIMESTAMP,
        last_train TIMESTAMP,
        last_factory TIMESTAMP,
        FOREIGN KEY(clan_id) REFERENCES clans(id) ON DELETE SET NULL
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS wars (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        attacker_id INTEGER,
        defender_id INTEGER,
        start_time TIMESTAMP,
        last_tick TIMESTAMP,
        white_peace_offer INTEGER DEFAULT NULL
    )''')
    
    conn.commit()
    conn.close()
