from discord.ext import commands
import d20

def setup(bot):
    @bot.command()
    async def roll(ctx, dice: str):
        """Roll dice (e.g., !roll 1d20+5)."""
        try:
            result = d20.roll(dice)
            await ctx.send(f'{ctx.author.mention} rolled: {result}')
        except Exception as e:
            await ctx.send(f'Invalid dice format! Use e.g., 1d20+5. Error: {str(e)}')