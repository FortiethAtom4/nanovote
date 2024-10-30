import discord, datetime, config, db
from discord.ext import commands

class CustomCommands(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot


def setup(bot: discord.Bot):
    bot.add_cog(CustomCommands(bot)) 