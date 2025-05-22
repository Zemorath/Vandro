from discord.ext import commands
import sqlite3
import json
from models.character import Character

def setup(bot):
    @bot.command()
    async def create_character(ctx, name: str, class_name: str, level: int):
        """Create a D&D 5e character.
        
        Usage: !create_character <name> <class> <level>
        Example: !create_character "Aragorn" Fighter 1
        """
        user_id = ctx.author.id
        stats = {
            "strength": 15,
            "dexterity": 14,
            "constitution": 13,
            "intelligence": 12,
            "wisdom": 10,
            "charisma": 8
        }
        skills = {
            "athletics": 2 if class_name.lower() in ["fighter", "barbarian"] else 0,
            "perception": 2 if class_name.lower() in ["ranger", "druid"] else 0,
            "arcana": 2 if class_name.lower() in ["wizard", "sorcerer"] else 0
        }
        hit_points = 10 + (level - 1) * 6 if class_name.lower() == "fighter" else 8 + (level - 1) * 5
        armor_class = 16 if class_name.lower() == "fighter" else 13
        proficiency_bonus = 2
        inventory = ["sword"] if class_name.lower() == "fighter" else ["staff"]
        spells = []  # Empty for non-casters
        feats = []
        
        character = Character(
            name=name,
            class_name=class_name,
            level=level,
            stats=stats,
            skills=skills,
            hit_points=hit_points,
            armor_class=armor_class,
            proficiency_bonus=proficiency_bonus,
            inventory=inventory
        )
        
        conn = sqlite3.connect('rpg_data.db')
        c = conn.cursor()
        c.execute('SELECT id, channel_id FROM campaigns WHERE status = "active" AND party LIKE ?', (f'%{user_id}%',))
        result = c.fetchone()
        if not result:
            await ctx.send("Error: You're not in an active campaign. Use !join_campaign first.")
            conn.close()
            return
        campaign_id, channel_id = result
        if ctx.channel.id != channel_id:
            await ctx.send(f"Error: This command must be used in the campaign's channel (ID: {channel_id}).")
            conn.close()
            return
        c.execute('INSERT INTO characters (campaign_id, user_id, name, class_name, level, stats, skills, hit_points, armor_class, proficiency_bonus, inventory, spells, feats) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                  (campaign_id, user_id, name, class_name, level, json.dumps(stats), json.dumps(skills), hit_points, armor_class, proficiency_bonus, json.dumps(inventory), json.dumps(spells), json.dumps(feats)))
        conn.commit()
        conn.close()
        
        await ctx.send(f'Character "{name}" created for {ctx.author.mention}! Class: {class_name}, Level: {level}, HP: {hit_points}, AC: {armor_class}, Stats: {stats}, Skills: {skills}')

    @bot.command()
    async def skill(ctx, skill_name: str):
        """Perform a D&D 5e skill check.
        
        Usage: !skill <skill_name>
        Example: !skill Perception
        """
        user_id = ctx.author.id
        conn = sqlite3.connect('rpg_data.db')
        c = conn.cursor()
        c.execute('SELECT id, channel_id FROM campaigns WHERE status = "active" AND party LIKE ?', (f'%{user_id}%',))
        result = c.fetchone()
        if not result:
            await ctx.send("Error: You're not in an active campaign.")
            conn.close()
            return
        campaign_id, channel_id = result
        if ctx.channel.id != channel_id:
            await ctx.send(f"Error: This command must be used in the campaign's channel (ID: {channel_id}).")
            conn.close()
            return
        
        c.execute('SELECT name, skills, stats, proficiency_bonus FROM characters WHERE user_id = ? AND campaign_id = ?', (user_id, campaign_id))
        character = c.fetchone()
        if not character:
            await ctx.send("Error: You don't have a character in this campaign.")
            conn.close()
            return
        
        char_name, skills_json, stats_json, proficiency_bonus = character
        skills = json.loads(skills_json)
        stats = json.loads(stats_json)
        
        skill_name = skill_name.lower()
        if skill_name not in skills:
            await ctx.send(f"Error: Invalid skill '{skill_name}'. Try: athletics, perception, arcana.")
            conn.close()
            return
        
        skill_to_stat = {
            "athletics": "strength",
            "perception": "wisdom",
            "arcana": "intelligence"
        }
        stat = skill_to_stat.get(skill_name, "strength")
        modifier = (stats[stat] - 10) // 2 + skills[skill_name]
        
        import d20
        result = d20.roll(f"1d20+{modifier}")
        await ctx.send(f"{char_name} performs a {skill_name} check: {result}")
        conn.close()

    @bot.command()
    async def level_up(ctx):
        """Level up your D&D 5e character.
        
        Usage: !level_up
        Example: !level_up
        """
        user_id = ctx.author.id
        conn = sqlite3.connect('rpg_data.db')
        c = conn.cursor()
        c.execute('SELECT id, channel_id FROM campaigns WHERE status = "active" AND party LIKE ?', (f'%{user_id}%',))
        result = c.fetchone()
        if not result:
            await ctx.send("Error: You're not in an active campaign.")
            conn.close()
            return
        campaign_id, channel_id = result
        if ctx.channel.id != channel_id:
            await ctx.send(f"Error: This command must be used in the campaign's channel (ID: {channel_id}).")
            conn.close()
            return
        
        c.execute('SELECT name, class_name, level, stats, hit_points, proficiency_bonus, spells, feats FROM characters WHERE user_id = ? AND campaign_id = ?', (user_id, campaign_id))
        character = c.fetchone()
        if not character:
            await ctx.send("Error: You don't have a character in this campaign.")
            conn.close()
            return
        
        name, class_name, level, stats_json, hit_points, proficiency_bonus, spells_json, feats_json = character
        stats = json.loads(stats_json)
        spells = json.loads(spells_json)
        feats = json.loads(feats_json)
        
        # Level up (simplified for MVP)
        new_level = level + 1
        new_hit_points = hit_points + (6 if class_name.lower() == "fighter" else 5)
        new_proficiency = 2 + (new_level - 1) // 4
        update_message = f"{name} levels up to {new_level}!\nHP: {hit_points} → {new_hit_points}\nProficiency: {new_proficiency}"
        
        # Ability Score Improvement or Feat (every 4 levels for Fighter)
        if new_level in [4, 8, 12, 16, 19] and class_name.lower() == "fighter":
            update_message += "\nChoose: +2 to one stat, +1 to two stats, or a feat (e.g., Great Weapon Master). Reply with your choice."
            # Simplified: Auto-apply +2 Strength
            stats['strength'] += 2
            update_message += "\nApplied: +2 Strength (default)."
        
        # Spells for casters (e.g., Wizard)
        if class_name.lower() == "wizard":
            spells.append(f"Level {new_level} spell (e.g., Fireball)")
            update_message += f"\nAdded a new spell (e.g., Fireball). Update with !set_spells."
        
        c.execute('UPDATE characters SET level = ?, hit_points = ?, proficiency_bonus = ?, stats = ?, spells = ?, feats = ? WHERE user_id = ? AND campaign_id = ?',
                  (new_level, new_hit_points, new_proficiency, json.dumps(stats), json.dumps(spells), json.dumps(feats), user_id, campaign_id))
        conn.commit()
        conn.close()
        
        await ctx.send(update_message)