import discord, datetime, config, utils.db as db, logging
from discord.ext import commands

logger = logging.getLogger(__name__)
logging.basicConfig(filename='mafia.log', encoding='utf-8', level=logging.INFO)

class CustomCommands(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot


def setup(bot: discord.Bot):
    bot.add_cog(CustomCommands(bot)) 