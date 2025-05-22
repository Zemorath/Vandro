import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect('rpg_data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS campaigns
                 (id INTEGER PRIMARY KEY, name TEXT, system TEXT, setting TEXT, status TEXT, last_updated TEXT, party TEXT, channel_id INTEGER, campaign_intro TEXT, milestones TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS characters
                 (id INTEGER PRIMARY KEY, campaign_id INTEGER, user_id INTEGER, name TEXT, class_name TEXT, level INTEGER, stats TEXT, skills TEXT, hit_points INTEGER, armor_class INTEGER, proficiency_bonus INTEGER, inventory TEXT, spells TEXT, feats TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS action_logs
                 (id INTEGER PRIMARY KEY, campaign_id INTEGER, user_id INTEGER, action TEXT, response TEXT, timestamp TEXT, pending_roll INTEGER, roll_context TEXT)''')
    conn.commit()
    conn.close()