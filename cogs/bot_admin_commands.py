import discord, datetime, config, utils.db as db
from discord.ext import commands

class BotAdminCommands(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    """
    /shutdown
    Allows the bot owner to force a bot shutdown remotely. Saves all mafia data before closing.
    """
    @discord.slash_command(
        name="shutdown",
        guild_ids=[config.GUILD_ID],
        description="BOT OWNER: Shuts the bot down."
    )
    @commands.is_owner()
    async def shutdown(self, ctx: discord.ApplicationContext):
        print("-> Updating...")
        db.persist_updates()
        print("-+ Update complete, shutting down")
        await ctx.respond("東雲の家は今日も平和であった。")
        await ctx.bot.close()
        exit()

    help: discord.SlashCommandGroup = discord.SlashCommandGroup(name="help",description="Various help commands",
                                                                guild_ids=[config.GUILD_ID])

    """
    /help player
    Shows a help message for players.
    """
    @help.command(
        description="Displays a help message for players."
    )
    async def player(self, ctx: discord.ApplicationContext):
        help_string: str = '''## PLAYER COMMANDS
All users have access to these commands.

- `/checktime`: Gets the amount of time left before the day ends.
- `/votecount`: Gets a list of all players in the game, their vote counts, the time remaining in the day, and the number of votes needed for majority.
- `/vote [playername]`: Places your vote for a player to be lynched. Available for living players only.
- `/unvote`: Revokes your vote on a player. Available for living players only.
- `/help player`: Displays this message.'''
        await ctx.respond(help_string,ephemeral=True)


    """
    /help mod
    Shows a help message for mods.
    """
    @commands.has_any_role("Moderator","Main Moderator")
    @help.command(
        description="Displays a help message for mods."
    )
    async def mod(self, ctx: discord.ApplicationContext):
        help_string: str = '''## MOD COMMANDS
Only users with the Moderator or Main Moderator roles can use these commands.
### SETUP
- `/addplayer [player_name] [player_username] [faction]`: Adds a player to the game. 
- `/help mod`: Displays this message.
- `/playerinfo`: Displays all information about living players in the game. This includes votecount info as well as their faction and vote value.
- `/removechannel`: Removes a voting flag from a channel.
- `/removelogchannel`: Removes a logging flag from a channel.
- `/setchannel`: Flags a channel for voting. Players may only vote in channels set with this command.
- `/setlogchannel`: Flags a channel for logging. The bot will record votes and unvotes in log channels.
- `/setmod`: Saves your username. You will be sent a DM when voting ends. NOTE: Only one username can be saved at a time. 
- `/unsetmod`: Removes your username from the bot. You will no longer be sent a DM if voting ends.
### TIMER
- `/settimer [time_hours] (time_minutes)`: Sets the timer for the day to end. Players can vote once the timer is started. The mod who sets this timer will be sent a DM when time is up.
- `/addtime [time_hours] (time_minutes)`: Adds time to the timer. Negative values subtract from the timer.
- `/toggletimer`: Toggles the timer on and off. Players cannot vote while the timer is off.
### VOTE MANAGEMENT
- `/resetvotes`: Resets all players' votes and sets their vote counts to 0.
- `/setvotevalue [player_name] [value]`: Sets the value of a player's vote. Default value is 1.
- `/addvotes [player_name] [value]`: Manually add votes to a player. Negative values subtract votes. WARNING: Adding votes this way CAN trigger majority.
### END OF DAY
- `/togglemajority`: Toggles the majority flag on or off. Players cannot vote if the majority flag is toggled. 
- `/kill [player_name]`: Kills a player, removing them from the game.'''
        await ctx.respond(help_string,ephemeral=True)




def setup(bot: discord.Bot):
    bot.add_cog(BotAdminCommands(bot)) 