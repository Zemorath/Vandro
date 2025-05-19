
# import discord
# from discord.ext import commands
# import sqlite3
# import os
# from dotenv import load_dotenv
# import d20
# from pydantic import BaseModel
# import json
# import aiohttp
# import asyncio
# from datetime import datetime

# # Load environment variables
# load_dotenv()
# TOKEN = os.getenv('DISCORD_TOKEN')
# GROK_API_KEY = os.getenv('GROK_API_KEY')

# # Set up bot with command prefix
# intents = discord.Intents.default()
# intents.message_content = True
# bot = commands.Bot(command_prefix='!', intents=intents)

# # Pydantic model for D&D 5e character
# class Character(BaseModel):
#     name: str
#     class_name: str
#     level: int
#     stats: dict  # Ability scores: strength, dexterity, etc.
#     skills: dict  # Skill proficiencies: athletics, perception, etc.
#     hit_points: int
#     armor_class: int
#     proficiency_bonus: int
#     inventory: list

# # Initialize SQLite database
# def init_db():
#     conn = sqlite3.connect('rpg_data.db')
#     c = conn.cursor()
#     c.execute('''CREATE TABLE IF NOT EXISTS campaigns
#                  (id INTEGER PRIMARY KEY, name TEXT, system TEXT, setting TEXT, status TEXT, last_updated TEXT, party TEXT)''')
#     c.execute('''CREATE TABLE IF NOT EXISTS characters
#                  (id INTEGER PRIMARY KEY, campaign_id INTEGER, user_id INTEGER, name TEXT, class_name TEXT, level INTEGER, stats TEXT, skills TEXT, hit_points INTEGER, armor_class INTEGER, proficiency_bonus INTEGER, inventory TEXT)''')
#     c.execute('''CREATE TABLE IF NOT EXISTS action_logs
#                  (id INTEGER PRIMARY KEY, campaign_id INTEGER, user_id INTEGER, action TEXT, response TEXT, timestamp TEXT)''')
#     conn.commit()
#     conn.close()

# @bot.event
# async def on_ready():
#     print(f'{bot.user} has connected to Discord!')
#     init_db()

# @bot.event
# async def on_command_error(ctx, error):
#     """Handle command errors gracefully."""
#     if isinstance(error, commands.MissingRequiredArgument):
#         await ctx.send(f"Error: Missing required argument `{error.param.name}`. Use `!help {ctx.command}` for usage.")
#     else:
#         await ctx.send(f"An error occurred: {str(error)}")
#         raise error

# @bot.command()
# async def start_campaign(ctx, name: str, system: str = "dnd5e", setting: str = "medieval fantasy", mode: str = "narrative"):
#     """Start a new campaign.
    
#     Usage: !start_campaign <name> [system] [setting] [mode]
#     Example: !start_campaign "Quest for Glory" dnd5e "dark fantasy" narrative
#     """
#     conn = sqlite3.connect('rpg_data.db')
#     c = conn.cursor()
#     c.execute('INSERT INTO campaigns (name, system, setting, status, last_updated, party) VALUES (?, ?, ?, ?, ?, ?)',
#               (name, system, setting, "active", datetime.now().isoformat(), json.dumps([ctx.author.id])))
#     campaign_id = c.lastrowid
#     conn.commit()
#     conn.close()
#     await ctx.send(f'Campaign "{name}" started! System: {system}, Setting: {setting}, Mode: {mode}. Use !join_campaign {campaign_id} to join.')

# @bot.command()
# async def join_campaign(ctx, campaign_id: int):
#     """Join an existing campaign.
    
#     Usage: !join_campaign <campaign_id>
#     Example: !join_campaign 1
#     """
#     conn = sqlite3.connect('rpg_data.db')
#     c = conn.cursor()
#     c.execute('SELECT party FROM campaigns WHERE id = ? AND status = "active"', (campaign_id,))
#     result = c.fetchone()
#     if not result:
#         await ctx.send(f"Error: Campaign ID {campaign_id} not found or inactive.")
#         conn.close()
#         return
#     party = json.loads(result[0])
#     if ctx.author.id in party:
#         await ctx.send(f"{ctx.author.mention}, you're already in this campaign!")
#         conn.close()
#         return
#     if len(party) >= 6:
#         await ctx.send(f"Error: Campaign {campaign_id} is full (max 6 players).")
#         conn.close()
#         return
#     party.append(ctx.author.id)
#     c.execute('UPDATE campaigns SET party = ? WHERE id = ?', (json.dumps(party), campaign_id))
#     conn.commit()
#     conn.close()
#     await ctx.send(f"{ctx.author.mention} joined campaign {campaign_id}! Use !create_character to add a character.")

# @bot.command()
# async def create_character(ctx, name: str, class_name: str, level: int):
#     """Create a D&D 5e character.
    
#     Usage: !create_character <name> <class> <level>
#     Example: !create_character "Aragorn" Fighter 1
#     """
#     user_id = ctx.author.id
#     # D&D 5e stats (standard array for simplicity)
#     stats = {
#         "strength": 15,
#         "dexterity": 14,
#         "constitution": 13,
#         "intelligence": 12,
#         "wisdom": 10,
#         "charisma": 8
#     }
#     # Simplified skills (proficiency in two class-appropriate skills)
#     skills = {
#         "athletics": 2 if class_name.lower() in ["fighter", "barbarian"] else 0,
#         "perception": 2 if class_name.lower() in ["ranger", "druid"] else 0,
#         "arcana": 2 if class_name.lower() in ["wizard", "sorcerer"] else 0
#     }
#     hit_points = 10 + (level - 1) * 6 if class_name.lower() == "fighter" else 8 + (level - 1) * 5
#     armor_class = 16 if class_name.lower() == "fighter" else 13  # Chain mail or leather
#     proficiency_bonus = 2  # Level 1
#     inventory = ["sword"] if class_name.lower() == "fighter" else ["staff"]
    
#     character = Character(
#         name=name,
#         class_name=class_name,
#         level=level,
#         stats=stats,
#         skills=skills,
#         hit_points=hit_points,
#         armor_class=armor_class,
#         proficiency_bonus=proficiency_bonus,
#         inventory=inventory
#     )
    
#     conn = sqlite3.connect('rpg_data.db')
#     c = conn.cursor()
#     c.execute('SELECT id FROM campaigns WHERE status = "active" AND party LIKE ?', (f'%{user_id}%',))
#     result = c.fetchone()
#     if not result:
#         await ctx.send("Error: You're not in an active campaign. Use !join_campaign first.")
#         conn.close()
#         return
#     campaign_id = result[0]
#     c.execute('INSERT INTO characters (campaign_id, user_id, name, class_name, level, stats, skills, hit_points, armor_class, proficiency_bonus, inventory) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
#               (campaign_id, user_id, name, class_name, level, json.dumps(stats), json.dumps(skills), hit_points, armor_class, proficiency_bonus, json.dumps(inventory)))
#     conn.commit()
#     conn.close()
    
#     await ctx.send(f'Character "{name}" created for {ctx.author.mention}! Class: {class_name}, Level: {level}, HP: {hit_points}, AC: {armor_class}, Stats: {stats}, Skills: {skills}')

# @bot.command()
# async def roll(ctx, dice: str):
#     """Roll dice (e.g., !roll 1d20+5)."""
#     try:
#         result = d20.roll(dice)
#         await ctx.send(f'{ctx.author.mention} rolled: {result}')
#     except Exception as e:
#         await ctx.send(f'Invalid dice format! Use e.g., 1d20+5. Error: {str(e)}')

# @bot.command()
# async def skill(ctx, skill_name: str):
#     """Perform a D&D 5e skill check.
    
#     Usage: !skill <skill_name>
#     Example: !skill Perception
#     """
#     user_id = ctx.author.id
#     conn = sqlite3.connect('rpg_data.db')
#     c = conn.cursor()
#     c.execute('SELECT name, skills, stats, proficiency_bonus FROM characters WHERE user_id = ? AND campaign_id IN (SELECT id FROM campaigns WHERE status = "active")', (user_id,))
#     character = c.fetchone()
#     if not character:
#         await ctx.send("Error: You don't have a character in an active campaign.")
#         conn.close()
#         return
    
#     char_name, skills_json, stats_json, proficiency_bonus = character
#     skills = json.loads(skills_json)
#     stats = json.loads(stats_json)
    
#     skill_name = skill_name.lower()
#     if skill_name not in skills:
#         await ctx.send(f"Error: Invalid skill '{skill_name}'. Try: athletics, perception, arcana.")
#         conn.close()
#         return
    
#     # Map skills to ability scores (simplified)
#     skill_to_stat = {
#         "athletics": "strength",
#         "perception": "wisdom",
#         "arcana": "intelligence"
#     }
#     stat = skill_to_stat.get(skill_name, "strength")
#     modifier = (stats[stat] - 10) // 2 + skills[skill_name]
    
#     result = d20.roll(f"1d20+{modifier}")
#     await ctx.send(f"{char_name} performs a {skill_name} check: {result}")
#     conn.close()

# @bot.event
# async def on_message(message):
#     """Handle plain English actions as GPT prompts."""
#     if message.author == bot.user or message.content.startswith('!'):
#         await bot.process_commands(message)
#         return
    
#     conn = sqlite3.connect('rpg_data.db')
#     c = conn.cursor()
#     c.execute('SELECT id, name, setting FROM campaigns WHERE status = "active" AND party LIKE ?', (f'%{message.author.id}%',))
#     campaign = c.fetchone()
#     if not campaign:
#         await bot.process_commands(message)
#         return
    
#     campaign_id, campaign_name, setting = campaign
#     c.execute('SELECT name, class_name, level, stats, skills, hit_points, armor_class FROM characters WHERE user_id = ? AND campaign_id = ?', (message.author.id, campaign_id))
#     character = c.fetchone()
    
#     action = message.content
#     system_prompt = (
#         f"You are a D&D 5e dungeon master for a {setting} campaign named '{campaign_name}'. "
#         f"Generate narrative responses for player actions, incorporating D&D 5e mechanics (e.g., dice rolls, stats). "
#         f"Keep responses concise (50-100 words) and advance the story. "
#         f"Player character: {character[0] if character else 'Unknown'}, Class: {character[1] if character else 'Unknown'}, Level: {character[2] if character else 1}, "
#         f"Stats: {json.loads(character[3]) if character else {}}, Skills: {json.loads(character[4]) if character else {}}, "
#         f"HP: {character[5] if character else 10}, AC: {character[6] if character else 10}."
#     )
    
#     async with aiohttp.ClientSession() as session:
#         async with session.post(
#             'https://api.x.ai/v1/chat/completions',
#             headers={
#                 'Content-Type': 'application/json',
#                 'Authorization': f'Bearer {GROK_API_KEY}'
#             },
#             json={
#                 'messages': [
#                     {'role': 'system', 'content': system_prompt},
#                     {'role': 'user', 'content': action}
#                 ],
#                 'model': 'grok-3-mini-latest',
#                 'stream': False,
#                 'temperature': 0.7,
#                 'max_tokens': 200
#             }
#         ) as resp:
#             if resp.status == 200:
#                 result = await resp.json()
#                 response = result['choices'][0]['message']['content']
#             else:
#                 response = f"Error: Failed to connect to Grok API (status {resp.status})."
    
#     c.execute('INSERT INTO action_logs (campaign_id, user_id, action, response, timestamp) VALUES (?, ?, ?, ?, ?)',
#               (campaign_id, message.author.id, action, response, datetime.now().isoformat()))
#     conn.commit()
#     conn.close()
    
#     await message.channel.send(response)
#     await bot.process_commands(message)

# # Run the bot
# bot.run(TOKEN)
