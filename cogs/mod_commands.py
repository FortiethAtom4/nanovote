import discord, datetime, config, utils.db as db
from discord.ext import commands

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
        guild_ids=[config.GUILD_ID],
        description="MOD: Sets a timer for the day to end."
    )
    @commands.has_any_role("Moderator","Main Moderator")
    async def set_timer(self, ctx: discord.ApplicationContext, time_hours: int, time_minutes: int = 0):
        tmp = datetime.timedelta(hours=time_hours, minutes=time_minutes)
        
        config.timer.start(tmp)

        print(f"-+ Timer set to {tmp}")
        await ctx.respond(f"Timer has been set to **{tmp}**, starting now.")


    '''
    /togglemajority
    '''
    @discord.slash_command(
        name="togglemajority",
        guild_ids=[config.GUILD_ID],
        description="MOD: toggles majority check."
    )
    @commands.has_any_role("Moderator","Main Moderator")
    async def toggle_majority(self, ctx: discord.ApplicationContext):
        config.majority = not config.majority
        config.timer.pause() if config.majority else config.timer.unpause()
        await ctx.respond(f"Majority flag set to `{config.majority}`.",ephemeral=True)

    '''
    /toggletimer
    '''
    @discord.slash_command(
        name="toggletimer",
        guild_ids=[config.GUILD_ID],
        description="MOD: Manually starts/stops the timer."
    )
    @commands.has_any_role("Moderator","Main Moderator")
    async def toggle_timer(self, ctx: discord.ApplicationContext):
        if config.timer.paused_or_stopped() == 0:
            await ctx.respond("Timer cannot be toggled as no time has been set. Use /settimer first.",ephemeral=True)
            return
        await ctx.respond(f"Timer {("started" if config.timer.toggle() else "stopped")}.")

    """
    /addtime
    Adds extra time to the timer.
    Works with negative values.
    """
    @discord.slash_command(
        name="addtime",
        guild_ids=[config.GUILD_ID],
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
                print(f"-+ Subtracted {datetime.timedelta(seconds=abs(total_seconds))} from the timer, time is now up")
                await ctx.respond(f"{datetime.timedelta(seconds=abs(total_seconds))} subtracted. Time is now up!")
                if config.mod_to_dm != None:
                    mod = await self.bot.fetch_user(config.mod_to_dm)
                    await mod.send("Time is up!")
                return
            print(f"-+ Subtracted {datetime.timedelta(seconds=abs(total_seconds))} from the timer")
            await ctx.respond(f"{datetime.timedelta(seconds=abs(total_seconds))} subtracted.")
        else:
            print(f"-+ Added {datetime.timedelta(seconds=abs(total_seconds))} to the timer")
            await ctx.respond(f"{time_added} added.")


    """
    /addplayer
    Persists a new Player object to the database.
    Includes name, Discord username, and their faction.
    """
    @discord.slash_command(
        name="addplayer",
        guild_ids=[config.GUILD_ID],
        description="MOD: Adds a player to a Mafia game."
    )
    @commands.has_any_role("Moderator","Main Moderator")

    async def add_player(self, ctx: discord.ApplicationContext, player_name: str, player_discord_username: str, faction: str):
        initial_response = await ctx.respond(f"Throwing {player_name}'s hat in the ring...",ephemeral=True)
        real_users = [member.name for member in ctx.bot.get_all_members()]
        if player_discord_username not in real_users:
            await initial_response.edit(content="That username does not exist. Please check your spelling and try again.")
            return
        
        print(f"-> Adding new player {player_name}...")
        return_message = ""
        match db.add_player(player_name, player_discord_username, faction):
            case 0:
                print("-+ Player added successfully")
                return_message = f"Player {player_name} ({player_discord_username}) successfully added."
            case 1:
                print("-- Player add failed")
                return_message = f"There was a problem adding this player. Please try again."
            case -1:
                print(f"-i Player {player_name} aleady in game, aborting")
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
        guild_ids=[config.GUILD_ID],
        description="MOD: displays all info about current players."
    )
    @commands.has_any_role("Moderator","Main Moderator")

    async def player_info(self, ctx: discord.ApplicationContext):
        initial_response = await ctx.respond("```Getting the deets...```",ephemeral=True)
        print("-> Getting all player info...")
        response_string = "```"
        if len(config.players) == 0:
            await initial_response.edit(content="```No players have been added yet.```")
        for player in config.players:
            response_string += player.to_string(True)
            response_string += "\n-----\n"
        response_string += "```"
        print("-+ Sent player info")
        await initial_response.edit(content=response_string)

    """
    /kill
    Kills a player.
    Removes all their votes and resets all votes on that player.
    """
    @discord.slash_command(
        name="kill",
        guild_ids=[config.GUILD_ID],
        description="MOD: Kills a player."
    )
    @commands.has_any_role("Moderator","Main Moderator")
    async def kill(self, ctx: discord.ApplicationContext, player_name: str):
        await ctx.response.defer(ephemeral=True)

        print(f"-> Killing {player_name}...")
        match db.kill_player(player_name):
            case 1:
                print(f"-- An error occurred when killing {player_name}")
                await ctx.respond("There was an unexpected error when processing the kill. Please try again.",ephemeral=True)

            case 0:
                print("-+ Kill successful")
                await ctx.respond(f"{player_name} has been killed. Remember to announce the death in daytime chat.",ephemeral=True)


    """
    /resetvotes
    Resets votes for all players and resets the majority check.
    """
    @discord.slash_command(
        name="resetvotes",
        guild_ids=[config.GUILD_ID],
        description="MOD: Reset all votes."
    )
    @commands.has_any_role("Moderator","Main Moderator")
    async def end_day(self, ctx: discord.ApplicationContext):

        print("-> Resetting all votes...")
        match db.end_day():
            case 0:
                print("-+ All votes reset")
                config.majority = False
                await ctx.respond("All votes have been reset.",ephemeral=True)

            case 1:
                print("-- An error occurred when resetting votes")
                await ctx.respond("There was an unexpected error resetting votes. Please try again.",ephemeral=True)

    """
    /setvotevalue
    Sets the value of a player's votes.
    Functions for both positive and negative values.
    """
    @discord.slash_command(
        name="setvotevalue",
        guild_ids=[config.GUILD_ID],
        description="MOD: Set the value of a player's votes."
    )
    @commands.has_any_role("Moderator","Main Moderator")
    async def set_vote_value(self, ctx: discord.ApplicationContext, player_name: str, value: int):
        print(f"-> Setting vote value of {player_name} to {value}...")
        match db.set_vote_value(player_name,value):
            case 1:
                print("-- An unexpected error occurred when setting vote value")
                await ctx.respond("There was an unexpected error setting vote value. Please try again.",ephemeral=True)
            case -1:
                print(f"-i Player {player_name} does not exist, aborting")
                await ctx.respond(f"Player {player_name} does not exist. Please check your spelling and try again.",ephemeral=True)
            case 0:
                print(f"-+ Player vote value set")
                await ctx.respond(f"{player_name}'s vote value has been set to {value}. NOTE: use /playerinfo to see players' vote values.",ephemeral=True)

    """
    /addvotes
    Adds or subtracts votes from a player.
    Subtraction is done with negative numbers.
    """
    @discord.slash_command(
        name="addvotes",
        guild_ids=[config.GUILD_ID],
        description="MOD: add or subtract votes from a player."
    )
    @commands.has_any_role("Moderator","Main Moderator")
    async def add_votes(self, ctx: discord.ApplicationContext, player_name: str, value: int):
        print(f"-> Adding {value} vote{"s" if value is not abs(1) else ""} to {player_name}...")
        match db.mod_add_vote(player_name,value):
            case 1:
                print(f"-- An unexpected error occurred when adding votes")
                await ctx.respond("Unexpected error, please try again",ephemeral=True)
            case -1:
                print(f"-i Player {player_name} not found, aborting")
                await ctx.respond(f"Player {player_name} does not exist. Please check your spelling and try again.",ephemeral=True)
            case 1000:
                config.majority = True
                print(f"-+ Successfully added, majority reached")
                await ctx.respond(f"Vote added to {player_name}. NOTE: A MAJORITY HAS BEEN REACHED. Voting has been disabled for your players.",ephemeral=True)
            case 0:
                print(f"-+ Successfully added")
                await ctx.respond(f"Vote added to {player_name}.",ephemeral=True)


    """
    /setchannel
    Persists a Discord channel to the 'channels' collection.
    Players are only permitted to use voting commands in channels set with this command.
    """
    @discord.slash_command(
        name="setchannel",
        guild_ids=[config.GUILD_ID],
        description="MOD: adds the current channel to the list of valid voting channels."
    )
    @commands.has_any_role("Moderator","Main Moderator")
    async def set_channel(self, ctx: discord.ApplicationContext):
        to_set = ctx.channel.id
        if to_set in config.valid_channel_ids:
            await ctx.respond("This channel is already set. Remove it with /removechannel.")
            print("-i Channel already set")
            return
        print("-> Adding new voting channel...")
        config.valid_channel_ids.append(ctx.channel.id)
        await ctx.respond(f"Channel set. Voting commands are now accessible from this channel.")

        print("-+ Channel added")


    """
    /removechannel
    Removes a channel from the 'channels' collection, disallowing voting in it.
    """
    @discord.slash_command(
        name="removechannel",
        guild_ids=[config.GUILD_ID],
        description="MOD: Removes the current channel from the list of valid voting channels."
    )
    @commands.has_any_role("Moderator","Main Moderator")
    async def remove_channel(self, ctx: discord.ApplicationContext):
        to_remove = int(ctx.channel.id)
        if to_remove not in config.valid_channel_ids:
            await ctx.respond("This channel has not been set for voting.")
            print("-i Channel has not been set for voting, skipping")
            return
        print("-> Removing voting channel...")
        config.valid_channel_ids.remove(to_remove)
        await ctx.respond("Voting commands are no longer accessible from this channel.")

        print("-+ Channel removed")

    """
    /setlogchannel
    Flags a channel to log voting and unvoting.
    Only one log channel can be set at a time.
    """
    @discord.slash_command(
        name="setlogchannel",
        guild_ids=[config.GUILD_ID],
        description="MOD: flags the current channel for logging voting events."
    )
    @commands.has_any_role("Moderator","Main Moderator")
    async def set_log_channel(self, ctx: discord.ApplicationContext):
        cur_channel = int(ctx.channel.id)
        if cur_channel in config.log_channel_ids:
            await ctx.respond("This channel is already set for logging. Remove it with /removelogchannel.")
            print("-i Channel already set")
            return

        print("-> Adding logging channel...")
        config.log_channel_ids.append(cur_channel)
        await ctx.respond("This channel has been flagged for logging events. Remove this flag with /removelogchannel.")
        print("-+ Channel added")

    """
    /removelogchannel
    Deletes the flagged channel ID, disabling logging for it.
    """
    @discord.slash_command(
        name="removelogchannel",
        guild_ids=[config.GUILD_ID],
        description="MOD: removes flag from the configured logging channel."
    )
    @commands.has_any_role("Moderator","Main Moderator")
    async def remove_log_channel(self, ctx: discord.ApplicationContext):
        to_remove = int(ctx.channel.id)
        if to_remove not in config.log_channel_ids:
            await ctx.respond("This channel does not have a logging flag to remove.")
            print("-i Log channel not set, skipping")
            return
        
        print("-> Removing logging channel...")
        config.log_channel_ids.remove(to_remove)
        await ctx.respond("Logging flag removed.")
        print("-+ Channel removed")

    """
    /setmod
    Saves the user's ID. That user will be sent a DM when majority is reached or if timer expires. 
    Currently, only one mod can receive DMS from the bot at a time. 
    """
    @discord.slash_command(
        name="setmod",
        guild_ids=[config.GUILD_ID],
        description="MOD: Saves your username. You will be sent a DM when voting ends."
    )
    @commands.has_any_role("Moderator","Main Moderator")
    async def set_mod_to_dm(self, ctx: discord.ApplicationContext):
        config.mod_to_dm = ctx.interaction.user.id
        await ctx.respond(f"Preferences saved. You will be sent a DM if majority is reached or if the timer expires.")
        print(f"-i User {self.bot.get_user(config.mod_to_dm)} flagged for bot DM when voting ends")

    """
    /unset
    removes the user's ID. That user will no longer be sent DMs from the bot. 
    """
    @discord.slash_command(
        name="unsetmod",
        guild_ids=[config.GUILD_ID],
        description="MOD: Removes your username from the bot. You will no longer be sent a DM if voting ends."
    )
    @commands.has_any_role("Moderator","Main Moderator")
    async def unset_mod_to_dm(self, ctx: discord.ApplicationContext):
        config.mod_to_dm = None
        await ctx.respond(f"Preferences saved.")
        print(f"-i Mod username removed, bot will no longer DM")


def setup(bot: discord.Bot): # this is called by Pycord to setup the cog
    bot.add_cog(ModCommands(bot)) # add the cog to the bot