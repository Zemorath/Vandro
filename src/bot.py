import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
from commands.campaign import setup as campaign_setup
from commands.character import setup as character_setup
from commands.dice import setup as dice_setup
from handlers.errors import setup as error_setup
from handlers.messages import setup as message_setup

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Set up bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Register commands and handlers
def setup_bot():
    campaign_setup(bot)
    character_setup(bot)
    dice_setup(bot)
    error_setup(bot)
    message_setup(bot)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

if __name__ == '__main__':
    setup_bot()
    bot.run(TOKEN)