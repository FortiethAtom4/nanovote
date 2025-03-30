import discord.ext
import discord, datetime, config, utils.db as db, logging, asyncio

import discord.ext.commands
from discord.ext import commands

logger = logging.getLogger(__name__)
logging.basicConfig(filename='mafia.log', encoding='utf-8', level=logging.INFO, format=config.log_formatter)

class ModCommands(commands.Cog):

    def __init__(self, bot: discord.Bot):
        self.bot = bot

    """ 
    /settimer
    Sets a timer for the mod for the day to end.
    Takes an integer value for number of hours.
    Optional minutes variable as well for partial hours.
    """
    @discord.slash_command(
        name="settimer",
        guild_ids=config.GUILD_IDS,
        description="MOD: Sets a timer for the day to end."
    )
    @commands.has_any_role("Moderator","Main Moderator")
    async def set_timer(self, ctx: discord.ApplicationContext, time_hours: int, time_minutes: int = 0):
        tmp = datetime.timedelta(hours=time_hours, minutes=time_minutes)
        
        config.timer.start(tmp)

        logger.info(f"Timer set to {tmp}")
        await ctx.respond(f"Timer has been set to **{tmp}**, starting now.")


    '''
    /togglemajority
    '''
    @discord.slash_command(
        name="togglemajority",
        guild_ids=config.GUILD_IDS,
        description="MOD: toggles majority check."
    )
    @commands.has_any_role("Moderator","Main Moderator")
    async def toggle_majority(self, ctx: discord.ApplicationContext):
        config.majority = not config.majority
        config.timer.pause() if config.majority else config.timer.unpause()
        logger.info(f"Majority flag set to {config.majority}")
        await ctx.respond(f"Majority flag set to `{config.majority}`.",ephemeral=True)

    '''
    /toggletimer
    '''
    @discord.slash_command(
        name="toggletimer",
        guild_ids=config.GUILD_IDS,
        description="MOD: Manually starts/stops the timer."
    )
    @commands.has_any_role("Moderator","Main Moderator")
    async def toggle_timer(self, ctx: discord.ApplicationContext):
        if config.timer.paused_or_stopped() == 0:
            await ctx.respond("Timer cannot be toggled as no time has been set. Use /settimer first.",ephemeral=True)
            return
        return_string = f"Timer {('started' if config.timer.toggle() else 'stopped')}."
        logger.info(return_string[:-1]) #getting rid of the punctuation makes it seems more techy
        await ctx.respond(return_string)

    """
    /addtime
    Adds extra time to the timer.
    Works with negative values.
    """
    @discord.slash_command(
        name="addtime",
        guild_ids=config.GUILD_IDS,
        description="MOD: Adds time to the timer. Negative values will subtract time instead."
    )
    @commands.has_any_role("Moderator","Main Moderator")
    async def add_time(self, ctx: discord.ApplicationContext, time_hours: int, time_minutes: int = 0):
        if config.timer.paused_or_stopped() == 0:
            await ctx.respond("Timer has not been set. Set it first with /settimer.")
        
        total_seconds = time_hours * 3600 + time_minutes * 60
        time_added = config.timer.add_time(time_hours,time_minutes)
        if total_seconds < 0:
            if config.timer.paused_or_stopped() == 0:
                logger.info(f"Subtracted {datetime.timedelta(seconds=abs(total_seconds))} from the timer, time is now up")
                await ctx.respond(f"{datetime.timedelta(seconds=abs(total_seconds))} subtracted. Time is now up!")
                if config.mod_to_dm != None:
                    mod = await self.bot.fetch_user(config.mod_to_dm)
                    await mod.send("Time is up!")
                    logger.info(f"Time up message sent to {config.mod_to_dm}")
                return
            logger.info(f"Subtracted {datetime.timedelta(seconds=abs(total_seconds))} from the timer")
            await ctx.respond(f"{datetime.timedelta(seconds=abs(total_seconds))} subtracted.")
        else:
            logger.info(f"Added {datetime.timedelta(seconds=abs(total_seconds))} to the timer")
            await ctx.respond(f"{time_added} added.")


    """
    /addplayer
    Persists a new Player object to the database.
    Includes name, Discord username, and their faction.
    """
    @discord.slash_command(
        name="addplayer",
        guild_ids=config.GUILD_IDS,
        description="MOD: Adds a player to a Mafia game."
    )
    @commands.has_any_role("Moderator","Main Moderator")

    async def add_player(self, ctx: discord.ApplicationContext, player_name: str, player_discord_username: str, faction: str):
        initial_response = await ctx.respond(f"Throwing {player_name}'s hat in the ring...",ephemeral=True)
        real_users = [member.name for member in ctx.bot.get_all_members()]
        if player_discord_username not in real_users:
            await initial_response.edit(content="That username does not exist. Please check your spelling and try again.")
            return
        
        logger.info(f"Adding new player {player_name}...")
        return_message = ""
        match db.add_player(player_name, player_discord_username, faction):
            case 0:
                logger.info("Player added successfully")
                return_message = f"Player {player_name} ({player_discord_username}) successfully added."
            case 1:
                logger.warning("Player add failed")
                return_message = f"There was a problem adding this player. Please try again."
            case -1:
                logger.info(f"Player {player_name} aleady in game, aborting")
                return_message = f"Player {player_name} ({player_discord_username}) is already in the game."

        await initial_response.edit(content=return_message)


    """ 
    /playerinfo
    An advanced form of /votecount that shows additional info about each player.
    This includes who each player has voted for, their vote's value, and their faction.
    Response is invisible to other players to avoid accidental info leaks.
    """
    @discord.slash_command(
        name="playerinfo",
        guild_ids=config.GUILD_IDS,
        description="MOD: displays all info about current players."
    )
    @commands.has_any_role("Moderator","Main Moderator")

    async def player_info(self, ctx: discord.ApplicationContext):
        initial_response = await ctx.respond("```Getting the deets...```",ephemeral=True)
        logger.info("Getting all player info...")
        response_string = "```"
        if len(config.players) == 0:
            await initial_response.edit(content="```No players have been added yet.```")
            logger.info("Empty response, no players in the game yet")
            return
        config.players = sorted(config.players, key=lambda player:player.name.lower())
        for player in config.players:
            response_string += player.to_string(True)
            response_string += "\n-----\n"
        response_string += "```"
        logger.info("Sent player info")
        await initial_response.edit(content=response_string)

    """
    /kill
    Kills a player.
    Removes all their votes and resets all votes on that player.
    """
    @discord.slash_command(
        name="kill",
        guild_ids=config.GUILD_IDS,
        description="MOD: Kills a player."
    )
    @commands.has_any_role("Moderator","Main Moderator")
    async def kill(self, ctx: discord.ApplicationContext, player_name: str):
        await ctx.response.defer(ephemeral=True)

        logger.info(f"Killing {player_name}...")
        match db.kill_player(player_name):
            case 1:
                logger.warning(f"An error occurred when killing {player_name}")
                await ctx.respond("There was an unexpected error when processing the kill. Please try again.",ephemeral=True)

            case 0:
                logger.info("Kill successful")
                await ctx.respond(f"{player_name} has been killed. Remember to announce the death in daytime chat.",ephemeral=True)


    """
    /resetvotes
    Resets votes for all players and resets the majority check.
    """
    @discord.slash_command(
        name="resetvotes",
        guild_ids=config.GUILD_IDS,
        description="MOD: Reset all votes."
    )
    @commands.has_any_role("Moderator","Main Moderator")
    async def end_day(self, ctx: discord.ApplicationContext):

        logger.info("Resetting all votes...")
        match db.end_day():
            case 0:
                logger.info("All votes reset")
                config.majority = False
                await ctx.respond("All votes have been reset.",ephemeral=True)

            case 1:
                logger.warning("An error occurred when resetting votes")
                await ctx.respond("There was an unexpected error resetting votes. Please try again.",ephemeral=True)

    """
    /setvotevalue
    Sets the value of a player's votes.
    Functions for both positive and negative values.
    """
    @discord.slash_command(
        name="setvotevalue",
        guild_ids=config.GUILD_IDS,
        description="MOD: Set the value of a player's votes."
    )
    @commands.has_any_role("Moderator","Main Moderator")
    async def set_vote_value(self, ctx: discord.ApplicationContext, player_name: str, value: int):
        logger.info(f"Setting vote value of {player_name} to {value}...")
        match db.set_vote_value(player_name,value):
            case 1:
                logger.info("An unexpected error occurred when setting vote value")
                await ctx.respond("There was an unexpected error setting vote value. Please try again.",ephemeral=True)
            case -1:
                logger.info(f"Player {player_name} does not exist, aborting")
                await ctx.respond(f"Player {player_name} does not exist. Please check your spelling and try again.",ephemeral=True)
            case 0:
                logger.info(f"Player vote value set")
                await ctx.respond(f"{player_name}'s vote value has been set to {value}. NOTE: use /playerinfo to see players' vote values.",ephemeral=True)

    """
    /addvotes
    Adds or subtracts votes from a player.
    Subtraction is done with negative numbers.
    """
    @discord.slash_command(
        name="addvotes",
        guild_ids=config.GUILD_IDS,
        description="MOD: add or subtract votes from a player."
    )
    @commands.has_any_role("Moderator","Main Moderator")
    async def add_votes(self, ctx: discord.ApplicationContext, player_name: str, value: int):
        logger.info(f"Adding {value} vote{'s' if value is not abs(1) else ''} to {player_name}...")
        match db.mod_add_vote(player_name,value):
            case 1:
                logger.warning(f"An unexpected error occurred when adding votes")
                await ctx.respond("Unexpected error, please try again",ephemeral=True)
            case -1:
                logger.info(f"Player {player_name} not found, aborting")
                await ctx.respond(f"Player {player_name} does not exist. Please check your spelling and try again.",ephemeral=True)
            case 1000:
                config.majority = True
                logger.info(f"Successfully added, majority reached")
                await ctx.respond(f"Vote added to {player_name}. NOTE: A MAJORITY HAS BEEN REACHED. Voting has been disabled for your players.",ephemeral=True)
            case 0:
                logger.info(f"Successfully added")
                await ctx.respond(f"Vote added to {player_name}.",ephemeral=True)


    """
    /setchannel
    Persists a Discord channel to the 'channels' collection.
    Players are only permitted to use voting commands in channels set with this command.
    """
    @discord.slash_command(
        name="setchannel",
        guild_ids=config.GUILD_IDS,
        description="MOD: adds the current channel to the list of valid voting channels."
    )
    @commands.has_any_role("Moderator","Main Moderator")
    async def set_channel(self, ctx: discord.ApplicationContext):
        to_set = ctx.channel.id
        logger.info("-> Adding new voting channel...")
        if to_set in config.valid_channel_ids:
            await ctx.respond("This channel is already set. Remove it with /removechannel.")
            logger.info("Channel already set, aborting")
            return
        config.valid_channel_ids.append(ctx.channel.id)
        await ctx.respond(f"Channel set. Voting commands are now accessible from this channel.")

        logger.info("Channel added")


    """
    /removechannel
    Removes a channel from the 'channels' collection, disallowing voting in it.
    """
    @discord.slash_command(
        name="removechannel",
        guild_ids=config.GUILD_IDS,
        description="MOD: Removes the current channel from the list of valid voting channels."
    )
    @commands.has_any_role("Moderator","Main Moderator")
    async def remove_channel(self, ctx: discord.ApplicationContext):
        to_remove = int(ctx.channel.id)
        logger.info("Removing voting channel...")
        if to_remove not in config.valid_channel_ids:
            await ctx.respond("This channel has not been set for voting.")
            logger.info("Channel has not been set for voting, skipping")
            return
        
        config.valid_channel_ids.remove(to_remove)
        await ctx.respond("Voting commands are no longer accessible from this channel.")

        logger.info("Channel removed")

    """
    /setlogchannel
    Flags a channel to log voting and unvoting.
    """
    @discord.slash_command(
        name="setlogchannel",
        guild_ids=config.GUILD_IDS,
        description="MOD: flags the current channel for logging voting events."
    )
    @commands.has_any_role("Moderator","Main Moderator")
    async def set_log_channel(self, ctx: discord.ApplicationContext):
        cur_channel = int(ctx.channel.id)
        logger.info("Adding logging channel...")
        if cur_channel in config.log_channel_ids:
            await ctx.respond("This channel is already set for logging. Remove it with /removelogchannel.")
            logger.info("Channel already set")
            return

        
        config.log_channel_ids.append(cur_channel)
        await ctx.respond("This channel has been flagged for logging events. Remove this flag with /removelogchannel.")
        logger.info("Channel added")

    """
    /removelogchannel
    Deletes the flagged channel ID, disabling logging for it.
    """
    @discord.slash_command(
        name="removelogchannel",
        guild_ids=config.GUILD_IDS,
        description="MOD: removes flag from the configured logging channel."
    )
    @commands.has_any_role("Moderator","Main Moderator")
    async def remove_log_channel(self, ctx: discord.ApplicationContext):
        to_remove = int(ctx.channel.id)
        logger.info("Removing logging channel...")
        if to_remove not in config.log_channel_ids:
            await ctx.respond("This channel does not have a logging flag to remove.")
            logger.info("Log channel not set, skipping")
            return
        
        config.log_channel_ids.remove(to_remove)
        await ctx.respond("Logging flag removed.")
        logger.info("Channel removed")

    """
    /setmod
    Saves the user's ID. That user will be sent a DM when majority is reached or if timer expires. 
    Currently, only one mod can receive DMS from the bot at a time. 
    """
    @discord.slash_command(
        name="setmod",
        guild_ids=config.GUILD_IDS,
        description="MOD: Saves your username. You will be sent a DM when voting ends."
    )
    @commands.has_any_role("Moderator","Main Moderator")
    async def set_mod_to_dm(self, ctx: discord.ApplicationContext):
        config.mod_to_dm = ctx.interaction.user.id
        await ctx.respond(f"Preferences saved. You will be sent a DM if majority is reached or if the timer expires.")
        logger.info(f"User {self.bot.get_user(config.mod_to_dm)} flagged for bot DM when voting ends")

    """
    /unset
    removes the user's ID. That user will no longer be sent DMs from the bot. 
    """
    @discord.slash_command(
        name="unsetmod",
        guild_ids=config.GUILD_IDS,
        description="MOD: Removes your username from the bot. You will no longer be sent a DM if voting ends."
    )
    @commands.has_any_role("Moderator","Main Moderator")
    async def unset_mod_to_dm(self, ctx: discord.ApplicationContext):
        config.mod_to_dm = None
        await ctx.respond(f"Preferences saved.")
        logger.info(f"Mod username removed, bot will no longer DM")

    """
    /getlogs
    Sends a copy of the bot's logs as a text file. 
    """
    @discord.slash_command(
        name="getlogs",
        guild_ids=config.GUILD_IDS,
        description="MOD: Sends a copy of the bot's logs as a text file."
    )
    @commands.has_any_role("Moderator","Main Moderator")
    async def get_logs(self, ctx: discord.ApplicationContext):
        await ctx.respond("This command is not yet ready. Please come back later.")
        # with open("mafia.log") as logs:
            # await ctx.channel.send(file=discord.File(logs,"mafia.log"))

    """
    /togglemod
    Toggles a player's role. If that player is a moderator, they will be given mod role, and vice versa.
    WARNING: be very careful that this is used on the correct user.
    """
    @discord.slash_command(
        name="togglemod",
        guild_ids=config.GUILD_IDS,
        description="MOD: Grants a user the Moderator role, or removes it if they have it."
    )
    @commands.has_any_role("Moderator","Main Moderator")
    async def toggle_mod(self, ctx, user: str):
        try:
            all_members = list([x.name for x in ctx.guild.members])
            if user not in all_members:
                await ctx.respond(f"User {user} does not exist. Please check your spelling and try again.")
                return
            
            user_member: discord.Member = None
            # this sucks
            for member in ctx.guild.members:
                if member.name == user:
                    user_member = member
                    break
            
            # this is weird, is there a simpler way to do this?
            guild: discord.Guild = self.bot.get_guild(ctx.guild.id)
            mod_role = guild.get_role(int(config.MOD_ID))
            if mod_role in user_member.roles:
                await user_member.remove_roles(mod_role)
                await ctx.respond(f"User {user_member.name} has lost the mod role.")
                logger.info(f"User {user_member.name} has lost the mod role")
            else:
                await user_member.add_roles(mod_role)
                await ctx.respond(f"User {user_member.name} has received the mod role.")
                logger.info(f"User {user_member.name} has gained the mod role")
        except discord.ext.commands.errors.MissingAnyRole:
            await ctx.respond("You do not have permission to use this command.")



    @discord.slash_command(
        name="newgame",
        guild_ids=config.GUILD_IDS,
        description="MOD: Clears all saved data."
    )
    @commands.has_any_role("Moderator","Main Moderator")
    async def new_game(self, ctx):
        await ctx.respond("Are you sure you want to start a new game from scratch? **This will remove all saved players and channels.** (type 'yes' or 'y' to confirm, type anything else to cancel.)")

        def check(m): # checking if it's the same user and channel
            return m.author == ctx.author and m.channel == ctx.channel

        try: # waiting for message
            response = await self.bot.wait_for('message', check=check, timeout=30.0) # timeout - how long bot waits for message (in seconds)
        except asyncio.TimeoutError: # returning after timeout
            await ctx.channel.send("Timed out.")
            return

        # if response is different than yes / y - return
        if response.content.lower() not in ("yes", "y"): # lower() makes everything lowercase to also catch: YeS, YES etc.
            await ctx.channel.send("Cancelled.")
            logger.info("Game not reset, user cancelled")
            return
        
        config.valid_channel_ids = []
        config.log_channel_ids = []
        config.players = []
        config.mod_to_dm = None
        config.timer.stop()
        db.persist_updates()
        await ctx.channel.send("Game data has been cleared.")
        logger.info("Game reset")
        
        
        

        
        
    


def setup(bot: discord.Bot): # this is called by Pycord to setup the cog
    bot.add_cog(ModCommands(bot)) # add the cog to the bot