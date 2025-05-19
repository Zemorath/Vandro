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
        c.execute('SELECT id, name, setting, channel_id FROM campaigns WHERE status = "active" AND party LIKE ?', (f'%{message.author.id}%',))
        campaign = c.fetchone()
        if not campaign or message.channel.id != campaign[3]:
            print(f"No active campaign or wrong channel for user {message.author.id}")
            await bot.process_commands(message)
            return
        
        campaign_id, campaign_name, setting, channel_id = campaign
        c.execute('SELECT name, class_name, level, stats, skills, hit_points, armor_class FROM characters WHERE user_id = ? AND campaign_id = ?', (message.author.id, campaign_id))
        character = c.fetchone()
        
        action = message.content
        system_prompt = (
            f"You are a D&D 5e dungeon master for a {setting} campaign named '{campaign_name}'. "
            f"Generate narrative responses for player actions, incorporating D&D 5e mechanics (e.g., dice rolls, stats). "
            f"Keep responses concise (50-100 words) and advance the story. "
            f"Player character: {character[0] if character else 'Unknown'}, Class: {character[1] if character else 'Unknown'}, Level: {character[2] if character else 1}, "
            f"Stats: {json.loads(character[3]) if character else {}}, Skills: {json.loads(character[4]) if character else {}}, "
            f"HP: {character[5] if character else 10}, AC: {character[6] if character else 10}."
        )
        
        response = await call_grok_api(system_prompt, action)
        
        c.execute('INSERT INTO action_logs (campaign_id, user_id, action, response, timestamp) VALUES (?, ?, ?, ?, ?)',
                  (campaign_id, message.author.id, action, response, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        
        await message.channel.send(response)
        await bot.process_commands(message)