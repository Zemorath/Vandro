
import discord
from discord.ext import commands
import sqlite3
import os
from dotenv import load_dotenv
import d20
from pydantic import BaseModel
import json

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GROK_API_KEY = os.getenv('GROK_API_KEY')  # Placeholder for Grok API key

# Set up bot with command prefix
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Pydantic model for character validation
class Character(BaseModel):
    name: str
    class_name: str
    level: int
    stats: dict

# Initialize SQLite database (temporary; will migrate to PostgreSQL)
def init_db():
    conn = sqlite3.connect('rpg_data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS campaigns
                 (id INTEGER PRIMARY KEY, name TEXT, system TEXT, setting TEXT, status TEXT, last_updated TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS characters
                 (id INTEGER PRIMARY KEY, campaign_id INTEGER, user_id INTEGER, name TEXT, class_name TEXT, level INTEGER, stats TEXT, inventory TEXT)''')
    conn.commit()
    conn.close()

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    init_db()

@bot.event
async def on_command_error(ctx, error):
    """Handle command errors gracefully."""
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Error: Missing required argument `{error.param.name}`. Use `!help {ctx.command}` for usage.")
    else:
        await ctx.send(f"An error occurred: {str(error)}")
        raise error  # Log unexpected errors for debugging

@bot.command()
async def start_campaign(ctx, name: str, system: str = "dnd5e", setting: str = "medieval fantasy", mode: str = "narrative"):
    """Start a new campaign.
    
    Usage: !start_campaign <name> [system] [setting] [mode]
    Example: !start_campaign "Quest for Glory" dnd5e "dark fantasy" narrative
    Args:
        name: Campaign name (required)
        system: RPG system (default: dnd5e)
        setting: Campaign setting (default: medieval fantasy)
        mode: Narrative mode (default: narrative)
    """
    conn = sqlite3.connect('rpg_data.db')
    c = conn.cursor()
    c.execute('INSERT INTO campaigns (name, system, setting, status, last_updated) VALUES (?, ?, ?, ?, datetime("now"))',
              (name, system, setting, "active"))
    campaign_id = c.lastrowid
    conn.commit()
    conn.close()
    await ctx.send(f'Campaign "{name}" started! System: {system}, Setting: {setting}, Mode: {mode}. Use !create_character to join.')

@bot.command()
async def create_character(ctx, name: str, class_name: str, level: int):
    """Create a D&D 5e character.
    
    Usage: !create_character <name> <class> <level>
    Example: !create_character "Aragorn" Fighter 1
    """
    user_id = ctx.author.id
    # Default D&D 5e stats (simplified for MVP)
    stats = {
        "strength": 10,
        "dexterity": 10,
        "constitution": 10,
        "intelligence": 10,
        "wisdom": 10,
        "charisma": 10
    }
    inventory = []
    character = Character(name=name, class_name=class_name, level=level, stats=stats)
    
    conn = sqlite3.connect('rpg_data.db')
    c = conn.cursor()
    # Assume the latest campaign for simplicity (improve in Phase 2)
    c.execute('SELECT id FROM campaigns WHERE status = "active" ORDER BY id DESC LIMIT 1')
    result = c.fetchone()
    if not result:
        await ctx.send("Error: No active campaigns found. Start a campaign with !start_campaign first.")
        conn.close()
        return
    campaign_id = result[0]
    c.execute('INSERT INTO characters (campaign_id, user_id, name, class_name, level, stats, inventory) VALUES (?, ?, ?, ?, ?, ?, ?)',
              (campaign_id, user_id, name, class_name, level, json.dumps(stats), json.dumps(inventory)))
    conn.commit()
    conn.close()
    
    await ctx.send(f'Character "{name}" created for {ctx.author.mention}! Class: {class_name}, Level: {level}, Stats: {stats}')

@bot.command()
async def roll(ctx, dice: str):
    """Roll dice (e.g., !roll 1d20+5)."""
    try:
        result = d20.roll(dice)
        await ctx.send(f'{ctx.author.mention} rolled: {result}')
    except Exception as e:
        await ctx.send(f'Invalid dice format! Use e.g., 1d20+5. Error: {str(e)}')

@bot.event
async def on_message(message):
    """Handle plain English actions as GPT prompts."""
    if message.author == bot.user or message.content.startswith('!'):
        await bot.process_commands(message)
        return
    
    # Check if message is in a campaign channel (simplify for MVP)
    conn = sqlite3.connect('rpg_data.db')
    c = conn.cursor()
    c.execute('SELECT id FROM campaigns WHERE status = "active" LIMIT 1')
    campaign = c.fetchone()
    conn.close()
    
    if campaign:
        # Stub for Grok API integration
        action = message.content
        response = f"[Grok API Placeholder] Processing action: {action}\nExample response: Your character swings their sword, striking the goblin!"
        await message.channel.send(response)
    
    await bot.process_commands(message)

# Run the bot
bot.run(TOKEN)
