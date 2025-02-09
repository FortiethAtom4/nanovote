import discord.ext
import discord, datetime, config, utils.db as db, logging, asyncio

import discord.ext.commands
from discord.ext import commands

logger = logging.getLogger(__name__)
logging.basicConfig(filename='mafia.log', encoding='utf-8', level=logging.INFO, format=config.log_formatter)

# Set of commands specifically relating to mafia-aligned players.
class MafiaCommands(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    mafia: discord.SlashCommandGroup = discord.SlashCommandGroup(name="mafia",description="Mafia-specific commands")

    """
    /mafia toggle
    Toggle players to become mafia members.
    """
    @mafia.command(
        description="MOD: Toggle a player as a member/non-member of mafia.",
    )
    @commands.has_any_role("Moderator","Main Moderator")
    async def player(self, ctx: discord.ApplicationContext, name: str):
       mafia_player = next((player for player in config.players if player.name.lower() == name.lower()),None)
       if mafia_player == None:
           await ctx.respond(f"Player \"{name}\" does not exist. Please check your spelling and try again.",ephemeral=True)
           return
       
       mafia_player.mafia = not mafia_player.mafia
       await ctx.respond(f"{mafia_player.name} is now flagged as a member of the mafia.",ephemeral=True) if mafia_player.mafia \
        else await ctx.respond(f"{mafia_player.name} is no longer flagged as a member of the mafia.",ephemeral=True)
        
    @mafia.command(
        description="MOD: Toggle a channel for mafia voting.",
    )
    @commands.has_any_role("Moderator","Main Moderator")
    async def channel(self, ctx: discord.ApplicationContext):
        if config.mafia_channel_id != None:
            if config.mafia_channel_id == ctx.channel.id:
                config.mafia_channel_id = None
                await ctx.respond("Channel unset. Scum commands have been disabled for your players.")
                return
            else:
                config.mafia_channel_id = ctx.channel.id
                await ctx.respond("Channel set. The mafia command channel has been swapped to this channel.")
                return

        config.mafia_channel_id = ctx.channel.id
        await ctx.respond("Channel set. This channel can now be used for scum commands.")

    """
    /mafia kill
    Choose a player to nightkill.
    """
    @mafia.command(
        description="MAFIA: Choose a player to nightkill."
    )
    async def kill(self, ctx: discord.ApplicationContext, killed_player: str):
       if ctx.channel.id != config.mafia_channel_id:
           await ctx.respond("Mafia scum commands are not allowed in this channel.")
           return
       
       user = next((player for player in config.players if player.username == ctx.user.name),None)
       if user == None:
           await ctx.respond("You are not in this game!")
           return
       
       if not user.mafia:
           await ctx.respond("You are not a member of mafia!")
           return
       
       if config.nightkilled_player != "":
           await ctx.respond(f"You have already chosen {config.nightkilled_player} to kill tonight.")
           return
       
       killed_user = next((player.name for player in config.players if player.name.lower() == killed_player.lower()),None)
       if killed_user == None:
           await ctx.respond(f"Player {killed_player} does not exist. Please check your spelling and try again.")
           return
       
       await ctx.respond(f"Are you sure you want to kill {killed_user}? **Once you have locked in this kill, you will not be able to change your mind.** (type 'yes' or 'y' to confirm, type anything else to cancel.)")
       def check(m): # checking if it's the same user and channel
            return m.author == ctx.author and m.channel == ctx.channel
       try: # waiting for message
            response = await self.bot.wait_for('message', check=check, timeout=30.0) # timeout - how long bot waits for message (in seconds)
       except asyncio.TimeoutError: # returning after timeout
            await ctx.channel.send("Timed out.")
            return
       if response.content.lower() not in ("yes", "y"): # lower() makes everything lowercase to also catch: YeS, YES etc.
            await ctx.channel.send("Cancelled.")
            logger.info("Player not locked in for kill, user cancelled")
            return
       
       config.nightkilled_player = killed_user
       await ctx.channel.send(f"{killed_user} has been locked in for tonight's kill.")
       logger.info(f"Player {killed_user} locked in for kill")

    """
    /mafia reset
    Reset the current chosen player.
    """
    @mafia.command(
        description="MOD: Reset the scum nightkill."
    )
    @commands.has_any_role("Moderator","Main Moderator")
    async def reset(self, ctx: discord.ApplicationContext):
        config.nightkilled_player = ""
        await ctx.respond("Reset complete. Scum can now choose a new player to nightkill.",ephemeral=True)

    """
    /mafia viewplayer
    View the current chosen player to nightkill.
    """
    @mafia.command(
        description="MAFIA/MOD: View tonight's chosen nightkill, if available."
    )
    async def viewplayer(self, ctx: discord.ApplicationContext):
        user = next((player for player in config.players if player.username == ctx.user.name),None)
        if user == None or not user.mafia:
            if "Moderator" not in [role.name for role in ctx.user.roles]:
                await ctx.respond("You are not allowed to use this command.",ephemeral=True)
                return
        
        if config.nightkilled_player == "":
            await ctx.respond("Mafia has not yet chosen a player to kill tonight.",ephemeral=True)
            return
        await ctx.respond(f"Mafia has locked in {config.nightkilled_player} to kill tonight.",ephemeral=True)


def setup(bot: discord.Bot):
    bot.add_cog(MafiaCommands(bot)) 