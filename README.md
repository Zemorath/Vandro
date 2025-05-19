# VandroDiscord RPG Bot
A Discord bot for playing D&D 5e tabletop RPG campaigns, powered by the Grok 3 Mini API for narrative generation.
Features

Start and join campaigns (!start_campaign, !join_campaign)
Create D&D 5e characters (!create_character)
Roll dice (!roll)
Perform skill checks (!skill)
Narrative responses for plain text actions in designated channels

Setup

Clone the repo.

Create a .env file with:
DISCORD_TOKEN=your_discord_bot_token
GROK_API_KEY=your_grok_api_key


Install dependencies:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt


Run the bot:
python src/bot.py



Deployment

Deploy to Render with a Python runtime, requirements.txt, and environment variables.
Set up PostgreSQL for production (TBD).

Future Features

Combat system
Action limits
PostgreSQL integration



