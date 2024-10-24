import discord, datetime, config, db
from discord.ext import commands

class PlayerCommands(commands.Cog):

    def __init__(self, bot: discord.Bot): # this is a special method that is called when the cog is loaded
        self.bot = bot

    """ 
    /checktime
    Sends a message stating the time left on the bot's timer.
    Checktime messages are private so as not to spam the chat with timers.
    If time needs to be seen publicly, use /votecount.
    """
    @discord.slash_command(
        name="checktime",
        guild_ids=[config.GUILD_ID],
        description="Gets the amount of time left."
    )
    async def check_time(self,ctx: discord.ApplicationContext):
        if not config.timer_on:
            await ctx.respond("Timer has not been set.",ephemeral=True)
            return
        tmp_format_time = datetime.timedelta(seconds=int((config.end_time - config.cur_time).total_seconds()))
        await ctx.respond(f"Time remaining: **{tmp_format_time}**",ephemeral=True)


    """ 
    /votecount
    Retrieves a list of all players in the game and their vote counts.
    Also displays the number of votes needed for majority and remaining time.
    """
    @discord.slash_command(
        name="votecount",
        guild_ids=[config.GUILD_ID],
        description="Gets all players in the game and their vote counts."
    )
    async def vote_count(self, ctx: discord.ApplicationContext):
        time_rem: datetime.timedelta = config.command_delay_timer - datetime.datetime.now()
        if time_rem > datetime.timedelta(seconds=0):
            await ctx.respond(f"Please wait {time_rem.seconds} second{"" if time_rem.seconds == 1 else "s"} before using /votecount again.",ephemeral=True)
            print("-+ Votecount spam prevented")
            return

        initial_response = await ctx.respond("```ini\n[Tallying votes...]```")
        print("-> Getting votecount...")

        players = db.get_all_players()
        majority_value = db.get_majority()

        if len(players) == 0:
            await initial_response.edit(content="No players have been added yet.")
            print("-i No players have been added yet")
            return
        
        response_string = "```ini\n[Votes:]\n"

        players = sorted(players, key=lambda player:player.name_lower)
        for player in players:
            response_string += player.to_string(False)+"\n"

        if config.majority:
            config.timer_on = False
            response_string += "\n[A majority has been reached.]\n"
        else:
            response_string += f"\n[With {len(players)} players, it takes {majority_value} votes to reach majority.]\n"

        tmp_format_time = datetime.timedelta(seconds=int((config.end_time - config.cur_time).total_seconds()))
        if config.timer_on:
            response_string += f"[{(f"Time remaining: {tmp_format_time}" if tmp_format_time > datetime.timedelta(seconds=0) else "Time is up!")}]\n"
        else:
            response_string += f"[Time remaining when majority was reached: {(tmp_format_time if tmp_format_time > datetime.timedelta(seconds=0) else datetime.timedelta(seconds=0))}]\n" if config.majority else "[Time is up!]\n"
        response_string += "```"
        print("-+ Sent votecount")
        await initial_response.edit(content=response_string)
        # increment anti-spam timer
        config.command_delay_timer = datetime.datetime.now() + datetime.timedelta(seconds=config.command_delay_seconds)

    """ 
    /vote
    Vote for a player to be lynched.
    Votes will be logged in a configured log channel.
    Will display a special message and disable voting commands if a majority is reached.
    """
    @discord.slash_command(
        name="vote",
        guild_ids=[config.GUILD_ID],
        description="Vote for a player to be lynched."
    )
    async def vote(self, ctx: discord.ApplicationContext, voted_for_name: str):

        if ctx.channel.id not in config.valid_channel_ids:
            await ctx.respond(content="Mafia commands are not allowed in this channel. Please ask an admin to use /setchannel or use the appropriate channels.")
            print("-i Vote sent in from a channel not flagged for voting commands, ignoring")
            return

        if config.majority:
            await ctx.respond("Majority has been reached. Voting commands have been disabled.")
            print("-i Majority reached, voting commands have been disabled")
            return
        
        if not config.timer_on:
            await ctx.respond("Time is up. Voting commands have been disabled.")
            print("-i Time is up, voting commands have been disabled")
            return
        
        username = ctx.user.name
        if not db.is_playing(username):
            await ctx.respond("You are not alive in this game!")
            print(f"-i Non-participating player {ctx.user.name} cannot vote")
            return
        
        initial_response = await ctx.respond("Sending your vote in...")
        voter_name = db.get_name_from_username(username)
        print(f"-> Sending in {voter_name}'s vote on {voted_for_name}...")
        match(db.vote(username,voted_for_name)):
            case -1:
                await initial_response.edit(content=f"You have already voted!")
                print(f"-i Player {ctx.user.name} has already voted")
            case 2:
                await initial_response.edit(content=f"Player \'{voted_for_name}\' does not exist. Please check your spelling and try again.")
                print(f"-i Player'{voted_for_name}' does not exist")
            case 1:
                await initial_response.edit(content=f"There was an unexpected error when processing vote for {voted_for_name}. Please try again.")
                print(f"-- An unexpected error occurred when sending in {ctx.user.name}'s vote for {voted_for_name}")
            case 1000:
                config.timer_on = False
                config.majority = True
                await initial_response.edit(content=f"You voted for {voted_for_name}. **MAJORITY REACHED**")
                mod = await self.bot.fetch_user(config.mod_to_dm)
                await mod.send("A majority has been reached!")
                resp: discord.Message = await initial_response.original_response()
                for c in config.log_channel_ids:
                    log_channel: discord.TextChannel = self.bot.get_channel(c)
                    await log_channel.send(f"[(LINK TO MESSAGE)]({resp.jump_url}) {voter_name} voted for {voted_for_name}. **MAJORITY REACHED**")
                print(f"-+ {voter_name} voted for {voted_for_name} and a majority was reached")
            case 0:
                await initial_response.edit(content=f"You voted for {voted_for_name}.")
                resp: discord.Message = await initial_response.original_response()
                for c in config.log_channel_ids:
                    log_channel: discord.TextChannel = self.bot.get_channel(c)
                    await log_channel.send(f"[(LINK TO MESSAGE)]({resp.jump_url}) {voter_name} voted for {voted_for_name}.")
                print(f"-+ {voter_name} voted for {voted_for_name}")
            

    """ 
    /unvote
    Revokes a player's vote.
    Unvotes will be logged in a configured log channel.
    """
    @discord.slash_command(
        name="unvote",
        guild_ids=[config.GUILD_ID],
        description="Revoke your vote on a player."
    )
    async def unvote(self, ctx: discord.ApplicationContext):

        if ctx.channel.id not in config.valid_channel_ids:
            await ctx.respond(content="Mafia commands are not allowed in this channel. Please ask an admin to use /setchannel or use the appropriate channels.")
            print("-i Vote sent in from a channel not flagged for voting commands, ignoring")
            return

        if config.majority:
            await ctx.respond("Majority has been reached. Voting commands have been disabled.")
            print("-i Majority reached, voting commands have been disabled")
            return
        
        if not config.timer_on:
            await ctx.respond("Time is up. Voting commands have been disabled.")
            print("-i Time is up, voting commands have been disabled")
            return
        
        username = ctx.user.name
        if not db.is_playing(username):
            await ctx.respond("You are not alive in this game!")
            print(f"-i Non-participating player {ctx.user.name} cannot unvote")
            return 
        
        initial_response = await ctx.respond("Striking thy name from the archives...")
        unvoter_name = db.get_name_from_username(username)
        print(f"-> {unvoter_name} is unvoting...")
        match(db.unvote(username)):
            case 1:
                print("-- An error occurred when processing unvote")
                await initial_response.edit(content="There was an unexpected error when processing your unvote. Please try again.")
            case -1:
                print(f"-i {unvoter_name} has not voted")
                await initial_response.edit(content="You haven't voted for anyone yet.")
            case 0:
                await initial_response.edit(content="You unvoted.")
                resp: discord.Message = await initial_response.original_response()
                for c in config.log_channel_ids:
                    log_channel: discord.TextChannel = self.bot.get_channel(c)
                    await log_channel.send(f"[(LINK TO MESSAGE)]({resp.jump_url}) {unvoter_name} unvoted.")

                print(f"-+ {unvoter_name} unvoted")

def setup(bot: discord.Bot): # this is called by Pycord to setup the cog
    bot.add_cog(PlayerCommands(bot)) # add the cog to the bot