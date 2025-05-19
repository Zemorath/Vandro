from discord.ext import commands

def setup(bot):
    @bot.event
    async def on_command_error(ctx, error):
        """Handle command errors gracefully."""
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Error: Missing required argument `{error.param.name}`. Use `!help {ctx.command}` for usage.")
        else:
            await ctx.send(f"An error occurred: {str(error)}")
            raise error