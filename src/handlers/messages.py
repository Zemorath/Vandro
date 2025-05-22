import discord
from discord.ext import commands
import sqlite3
import json
from datetime import datetime
from api.grok import call_grok_api

def setup(bot):
    @bot.event
    async def on_message(message):
        print(f"Received message from {message.author.id} in channel {message.channel.id}: {message.content}")
        if message.author == bot.user or message.content.startswith('!'):
            await bot.process_commands(message)
            return
        
        conn = sqlite3.connect('rpg_data.db')
        c = conn.cursor()
        c.execute('SELECT id, name, setting, channel_id, milestones FROM campaigns WHERE status = "active" AND party LIKE ? AND channel_id = ?',
                  (f'%{message.author.id}%', message.channel.id))
        campaign = c.fetchone()
        if not campaign:
            print(f"No active campaign for user {message.author.id} in channel {message.channel.id}")
            await bot.process_commands(message)
            conn.close()
            return
        
        campaign_id, campaign_name, setting, channel_id, milestones = campaign
        c.execute('SELECT name, class_name, level, stats, skills, hit_points, armor_class FROM characters WHERE user_id = ? AND campaign_id = ?',
                  (message.author.id, campaign_id))
        character = c.fetchone()
        
        action = message.content.lower()
        # Check for pending roll response
        c.execute('SELECT action, roll_context FROM action_logs WHERE campaign_id = ? AND user_id = ? AND pending_roll = 1 ORDER BY id DESC LIMIT 1',
                  (campaign_id, message.author.id))
        pending = c.fetchone()
        
        if pending:
            # Handle roll result (assume action is the roll result, e.g., "15")
            prev_action, roll_context = pending
            system_prompt = (
                f"D&D 5e DM for '{campaign_name}' ({setting}). Continue the narrative for '{prev_action}' using roll result '{action}' (from {roll_context}). "
                f"Respond in 50-100 words with mechanics. Character: {character[0]} (Level {character[2]} {character[1]}), "
                f"Stats: {json.loads(character[3])}, HP: {character[5]}, AC: {character[6]}. Exclude reasoning."
            )
        else:
            # Check if action requires a roll
            roll_required = any(keyword in action for keyword in ['attack', 'check', 'cast', 'persuade', 'stealth'])
            roll_context = None
            if roll_required:
                # Example: Attack uses STR modifier + proficiency (Fighter: +5)
                stat_mod = (json.loads(character[3])['strength'] - 10) // 2 if character else 0
                proficiency = character[4] if character else 2
                roll_context = f"1d20+{stat_mod + proficiency}"
                system_prompt = (
                    f"D&D 5e DM for '{campaign_name}' ({setting}). For actions needing a roll (e.g., attack), return 'Roll {roll_context} for [action].' "
                    f"Character: {character[0]} (Level {character[2]} {character[1]}), Stats: {json.loads(character[3])}, HP: {character[5]}, AC: {character[6]}. Exclude reasoning."
                )
            else:
                system_prompt = (
                    f"D&D 5e DM for '{campaign_name}' ({setting}). Respond in 50-100 words with narrative and mechanics. Include NPCs and non-combat options for enemies. "
                    f"Character: {character[0]} (Level {character[2]} {character[1]}), Stats: {json.loads(character[3])}, HP: {character[5]}, AC: {character[6]}. Exclude reasoning."
                )
        
        try:
            response = await call_grok_api(system_prompt, action, max_tokens=1000)
            print(f"Final response: {response}")
            if not response or response.strip() == "":
                response = "Error: Unable to generate a response from Grok API."
                print("Empty or invalid API response")
        except Exception as e:
            response = f"Error: Failed to process action: {str(e)}"
            print(f"Grok API error: {str(e)}")
        
        if not response:
            response = "Error: Unable to generate a response. Please try again."
        
        # Store action and check for milestones
        pending_roll = 1 if roll_required and "Roll" in response else 0
        c.execute('INSERT INTO action_logs (campaign_id, user_id, action, response, timestamp, pending_roll, roll_context) VALUES (?, ?, ?, ?, ?, ?, ?)',
                  (campaign_id, message.author.id, action, response, datetime.now().isoformat(), pending_roll, roll_context))
        conn.commit()
        
        # Check for level-up milestone (simplified keyword check)
        milestones = json.loads(milestones) if milestones else []
        if any(milestone.lower() in response.lower() for milestone in milestones):
            response += f"\n{character[0]}, you've reached a milestone! Level up with !level_up."
        
        await message.channel.send(response)
        conn.close()
        await bot.process_commands(message)