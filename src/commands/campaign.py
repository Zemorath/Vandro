from discord.ext import commands
import sqlite3
import json
from datetime import datetime
from api.grok import call_grok_api

def setup(bot):
    @bot.command()
    async def start_campaign(ctx, name: str, system: str = "dnd5e", setting: str = "medieval fantasy", mode: str = "narrative"):
        """Start a new campaign.
        
        Usage: !start_campaign <name> [system] [setting] [mode]
        Example: !start_campaign "Quest for Glory" dnd5e "dark fantasy" narrative
        """
        # Generate campaign introduction
        intro_prompt = (
            f"D&D 5e DM for '{name}' ({setting}). Create a 100-150 word campaign introduction outlining the narrative, themes, and rules. "
            f"Include 2-3 NPCs (names, roles). Mark 3 level-up milestones (e.g., major quests). Allow non-combat enemy resolutions. Adapt to player actions. Exclude reasoning."
        )
        try:
            campaign_intro = await call_grok_api(intro_prompt, "Generate campaign introduction.", max_tokens=400)
            if not campaign_intro or campaign_intro.startswith("Error"):
                campaign_intro = f"Welcome to {name}, a {setting} adventure! Rules: Use !roll for actions, interact with NPCs, negotiate with enemies. Milestones: 3 major quests."
        except Exception as e:
            campaign_intro = f"Welcome to {name}, a {setting} adventure! Rules: Use !roll for actions, interact with NPCs, negotiate with enemies. Milestones: 3 major quests."
        
        # Default milestones if GPT fails
        milestones = json.dumps(["Defeat the Bandit Lord", "Find the Temple Relic", "Confront the Dark God"])
        
        conn = sqlite3.connect('rpg_data.db')
        c = conn.cursor()
        c.execute('INSERT INTO campaigns (name, system, setting, status, last_updated, party, channel_id, campaign_intro, milestones) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                  (name, system, setting, "active", datetime.now().isoformat(), json.dumps([ctx.author.id]), ctx.channel.id, campaign_intro, milestones))
        campaign_id = c.lastrowid
        conn.commit()
        conn.close()
        
        await ctx.send(f'Campaign "{name}" started in this channel! System: {system}, Setting: {setting}, Mode: {mode}.\n\n{campaign_intro}\n\nUse !join_campaign {campaign_id} to join.')

    @bot.command()
    async def join_campaign(ctx, campaign_id: int):
        """Join an existing campaign.
        
        Usage: !join_campaign <campaign_id>
        Example: !join_campaign 1
        """
        conn = sqlite3.connect('rpg_data.db')
        c = conn.cursor()
        c.execute('SELECT party, channel_id FROM campaigns WHERE id = ? AND status = "active"', (campaign_id,))
        result = c.fetchone()
        if not result:
            await ctx.send(f"Error: Campaign ID {campaign_id} not found or inactive.")
            conn.close()
            return
        party, channel_id = json.loads(result[0]), result[1]
        if ctx.channel.id != channel_id:
            await ctx.send(f"Error: This command must be used in the campaign's channel (ID: {channel_id}).")
            conn.close()
            return
        if ctx.author.id in party:
            await ctx.send(f"{ctx.author.mention}, you're already in this campaign!")
            conn.close()
            return
        if len(party) >= 6:
            await ctx.send(f"Error: Campaign {campaign_id} is full (max 6 players).")
            conn.close()
            return
        party.append(ctx.author.id)
        c.execute('UPDATE campaigns SET party = ? WHERE id = ?', (json.dumps(party), campaign_id))
        conn.commit()
        conn.close()
        await ctx.send(f"{ctx.author.mention} joined campaign {campaign_id}! Use !create_character to add a character.")