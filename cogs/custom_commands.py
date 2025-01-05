import discord, datetime, config, utils.db as db, logging
from discord.ext import commands

logger = logging.getLogger(__name__)
logging.basicConfig(filename='mafia.log', encoding='utf-8', level=logging.INFO, format=config.log_formatter)

# Use this file to add your own suite of custom commands to the bot. 
# Feel free to edit this file as you see fit.
# Try copy/pasting command functions from other cog files into the class below if you aren't sure where to start.
class CustomCommands(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot


def setup(bot: discord.Bot):
    bot.add_cog(CustomCommands(bot)) 