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
        c.execute('SELECT id, name, setting, channel_id FROM campaigns WHERE status = "active" AND party LIKE ? AND channel_id = ?',
                  (f'%{message.author.id}%', message.channel.id))
        campaign = c.fetchone()
        if not campaign:
            print(f"No active campaign for user {message.author.id} in channel {message.channel.id}")
            await bot.process_commands(message)
            conn.close()
            return
        
        campaign_id, campaign_name, setting, channel_id = campaign
        c.execute('SELECT name, class_name, level, stats, skills, hit_points, armor_class FROM characters WHERE user_id = ? AND campaign_id = ?',
                  (message.author.id, campaign_id))
        character = c.fetchone()
        
        action = message.content
        system_prompt = (
            f"D&D 5e DM for '{campaign_name}' ({setting}). Respond in 50-100 words with narrative and mechanics (e.g., dice rolls). "
            f"Character: {character[0] if character else 'Unknown'} (Level {character[2] if character else 1} {character[1] if character else 'Unknown'}), "
            f"Stats: {json.loads(character[3]) if character else {}}, HP: {character[5] if character else 10}, AC: {character[6] if character else 10}. "
            f"Exclude reasoning or meta-text. Action: {action}"
        )
        
        try:
            response = await call_grok_api(system_prompt, action)
            print(f"Final response: {response}")
            if not response or response.strip() == "":
                response = "Error: Unable to generate a response from Grok API."
                print("Empty or invalid API response")
        except Exception as e:
            response = f"Error: Failed to process action: {str(e)}"
            print(f"Grok API error: {str(e)}")
        
        if not response:
            response = "Error: Unable to generate a response. Please try again."
        
        c.execute('INSERT INTO action_logs (campaign_id, user_id, action, response, timestamp) VALUES (?, ?, ?, ?, ?)',
                  (campaign_id, message.author.id, action, response, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        
        await message.channel.send(response)
        await bot.process_commands(message)