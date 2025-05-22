from discord.ext import commands
import d20
import sqlite3
import json
from datetime import datetime
from api.grok import call_grok_api

def setup(bot):
    @bot.command()
    async def roll(ctx, dice: str):
        """Roll dice (e.g., !roll 1d20+5)."""
        try:
            result = d20.roll(dice)
            response = f'{ctx.author.mention} rolled: {result}'
            
            # Check for pending roll
            conn = sqlite3.connect('rpg_data.db')
            c = conn.cursor()
            c.execute('SELECT id, action, roll_context, campaign_id FROM action_logs WHERE user_id = ? AND pending_roll = 1 ORDER BY id DESC LIMIT 1',
                      (ctx.author.id,))
            pending = c.fetchone()
            
            if pending:
                log_id, prev_action, roll_context, campaign_id = pending
                c.execute('SELECT name, setting, channel_id FROM campaigns WHERE id = ?', (campaign_id,))
                campaign = c.fetchone()
                if campaign and ctx.channel.id == campaign[2]:
                    c.execute('SELECT name, class_name, level, stats, hit_points, armor_class FROM characters WHERE user_id = ? AND campaign_id = ?',
                              (ctx.author.id, campaign_id))
                    character = c.fetchone()
                    system_prompt = (
                        f"D&D 5e DM for '{campaign[0]}' ({campaign[1]}). Continue narrative for '{prev_action}' using roll result '{result}' (from {roll_context}). "
                        f"Respond in 50-100 words with mechanics. Character: {character[0]} (Level {character[2]} {character[1]}), "
                        f"Stats: {json.loads(character[3])}, HP: {character[5]}, AC: {character[6]}. Exclude reasoning."
                    )
                    gpt_response = await call_grok_api(system_prompt, f"Roll result: {result}", max_tokens=400)
                    if not gpt_response or gpt_response.strip() == "":
                        gpt_response = "Error: Unable to generate a response from Grok API."
                    
                    c.execute('UPDATE action_logs SET response = ?, pending_roll = 0, timestamp = ? WHERE id = ?',
                              (gpt_response, datetime.now().isoformat(), log_id))
                    conn.commit()
                    response += f"\n{gpt_response}"
            
            conn.close()
            await ctx.send(response)
        except Exception as e:
            await ctx.send(f'Invalid dice format! Use e.g., 1d20+5. Error: {str(e)}')