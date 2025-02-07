import discord, datetime, config, utils.db as db, logging
from discord.ext import commands

logger = logging.getLogger(__name__)
logging.basicConfig(filename='mafia.log', encoding='utf-8', level=logging.INFO, format=config.log_formatter)

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
        guild_ids=config.GUILD_IDS,
        description="Gets the amount of time left."
    )
    async def check_time(self,ctx: discord.ApplicationContext):
        match config.timer.paused_or_stopped():
            case 0:
                await ctx.respond("Timer has not been set.",ephemeral=True)
            case 1:
                await ctx.respond(f"Timer stopped. Time remaining: **{config.timer.print_timer()}**",ephemeral=True)
            case 2:
                await ctx.respond(f"Time remaining: **{config.timer.print_timer()}**",ephemeral=True)


    """ 
    /votecount
    Retrieves a list of all players in the game and their vote counts.
    Also displays the number of votes needed for majority and remaining time.
    """
    @discord.slash_command(
        name="votecount",
        guild_ids=config.GUILD_IDS,
        description="Gets all players in the game and their vote counts."
    )
    async def vote_count(self, ctx: discord.ApplicationContext):
        time_rem: datetime.timedelta = config.command_delay_timer - datetime.datetime.now()
        if time_rem > datetime.timedelta(seconds=0):
            await ctx.respond(f"```ini\n[Please wait {time_rem.seconds} second{"" if time_rem.seconds == 1 else "s"} before using /votecount again.]```",ephemeral=True)
            logger.info("Votecount spam prevented")
            return

        # initial_response = await ctx.respond("```ini\n[Tallying votes...]```")
        logger.debug("Getting votecount...")

        majority_value = int(db.get_majority())
        
        if len(config.players) == 0:
            await ctx.respond(content="```ini\n[No players have been added yet.]```")
            logger.debug("No players have been added yet")
            return
        
        players_sorted = sorted(config.players, key=lambda player:player.name.lower())
        not_voted: str = "\n[Not voting: " # list of all players not voting
        response_string: str = "```ini\n[Votes:]\n"

        
        for player in players_sorted:
            response_string += player.to_string(False)+"\n"
            if player.voted_for == "":
                not_voted += f"{player.name}, "
        response_string += not_voted.removesuffix(", ") + "]\n"
        if config.majority:
            response_string += "\n[A majority has been reached.]\n"
        else:
            response_string += f"\n[With {len(players_sorted)} players, it takes {majority_value} votes to reach majority.]\n"

        match config.timer.paused_or_stopped():
            case 2:
                response_string += f"[Time remaining: {config.timer.print_timer()}]\n"

            case 1:
                response_string += f"[Timer stopped. Time remaining: {config.timer.print_timer()}]\n"

            case 0:
                response_string += "[Time is up!]"
        response_string += "```"
        log_player_str: str = ""
        for p in config.players:
            log_player_str += f"{p.name}: {p.number_of_votes} {p.votes}"
        logger.info(f"Sent votecount: [{log_player_str}]")
        await ctx.respond(content=response_string)
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
        guild_ids=config.GUILD_IDS,
        description="Vote for a player to be lynched."
    )
    async def vote(self, ctx: discord.ApplicationContext, voted_for_name: str):

        if ctx.channel.id not in config.valid_channel_ids:
            await ctx.respond(content="Mafia commands are not allowed in this channel. Please ask an admin to use /setchannel or use the appropriate channels.")
            logger.info("Vote sent in from a channel not flagged for voting commands, ignoring")
            return

        if config.majority:
            await ctx.respond("Majority has been reached. Voting commands have been disabled.")
            logger.debug("Majority reached, voting commands have been disabled")
            return
        
        if config.timer.paused_or_stopped() != 2:
            await ctx.respond("The timer has been stopped. Voting commands have been disabled.")
            logger.debug("Timer stopped, voting commands have been disabled")
            return
        
        username = ctx.user.name
        if not db.is_playing(username):
            await ctx.respond("You are not alive in this game!")
            logger.info(f"Non-participating player {ctx.user.name} cannot vote")
            return
        
        initial_response = await ctx.respond("Sending your vote in...")
        voter_name = next(player for player in config.players if player.username == username).name
        logger.debug(f"-> Sending in {voter_name}'s vote on {voted_for_name}...")
        match(db.vote(username,voted_for_name)):
            case -1:
                await initial_response.edit(content=f"You have already voted!")
                logger.debug(f"Player {ctx.user.name} has already voted")
            case 2:
                await initial_response.edit(content=f"Player \'{voted_for_name}\' does not exist. Please check your spelling and try again.")
                logger.debug(f"Player'{voted_for_name}' does not exist")
            case 1:
                await initial_response.edit(content=f"There was an unexpected error when processing vote for {voted_for_name}. Please try again.")
                logger.warning(f"An unexpected error occurred when sending in {ctx.user.name}'s vote for {voted_for_name}")
            case 1000:
                voted_for_name = next(player for player in config.players if player.name.lower() == voted_for_name.lower()).name # get the name with the capital letter
                await initial_response.edit(content=f"You voted for {voted_for_name}. **MAJORITY REACHED**")
                if config.mod_to_dm != None:
                    mod = await self.bot.fetch_user(config.mod_to_dm)
                    await mod.send("A majority has been reached!")
                resp: discord.Message = await initial_response.original_response()
                for c in config.log_channel_ids:
                    log_channel: discord.TextChannel = self.bot.get_channel(c)
                    await log_channel.send(f"[{voter_name} voted for {voted_for_name}.]({resp.jump_url}) **MAJORITY REACHED**")
                logger.info("Majority reached by vote, peristing updates...")
                db.persist_updates()
                logger.info("Updates persisted to database")
                config.timer.pause()
                config.majority = True
                logger.info(f"{voter_name} voted for {voted_for_name} and a majority was reached")
            case 0:
                voted_for_name = next(player for player in config.players if player.name.lower() == voted_for_name.lower()).name 
                await initial_response.edit(content=f"You voted for {voted_for_name}.")
                resp: discord.Message = await initial_response.original_response()
                for c in config.log_channel_ids:
                    log_channel = self.bot.get_channel(c)
                    await log_channel.send(f"[{voter_name} voted for {voted_for_name}.]({resp.jump_url})")
                logger.info(f"{voter_name} voted for {voted_for_name}")
            

    """ 
    /unvote
    Revokes a player's vote.
    Unvotes will be logged in a configured log channel.
    """
    @discord.slash_command(
        name="unvote",
        guild_ids=config.GUILD_IDS,
        description="Revoke your vote on a player."
    )
    async def unvote(self, ctx: discord.ApplicationContext):

        if ctx.channel.id not in config.valid_channel_ids:
            await ctx.respond(content="Mafia commands are not allowed in this channel. Please ask an admin to use /setchannel or use the appropriate channels.")
            logger.info("Vote sent in from a channel not flagged for voting commands, ignoring")
            return

        if config.majority:
            await ctx.respond("Majority has been reached. Voting commands have been disabled.")
            logger.debug("Majority reached, voting commands have been disabled")
            return

        if config.timer.paused_or_stopped() != 2:
            await ctx.respond("The timer has been stopped. Voting commands have been disabled.")
            logger.debug("Timer stopped, voting commands have been disabled")
            return
        
        username = ctx.user.name
        if not db.is_playing(username):
            await ctx.respond("You are not alive in this game!")
            logger.info(f"Non-participating player {ctx.user.name} cannot unvote")
            return 
        
        initial_response = await ctx.respond("Striking thy name from the archives...")
        unvoter_name = next(player for player in config.players if player.username == username).name
        logger.debug(f"{unvoter_name} is unvoting...")
        match(db.unvote(username)):
            case 1:
                logger.warning(f"An error occurred when processing unvote for {unvoter_name}")
                await initial_response.edit(content="There was an unexpected error when processing your unvote. Please try again.")
            case -1:
                logger.debug(f"-i {unvoter_name} has not voted")
                await initial_response.edit(content="You haven't voted for anyone yet.")
            case 0:
                await initial_response.edit(content="You unvoted.")
                resp: discord.Message = await initial_response.original_response()
                for c in config.log_channel_ids:
                    log_channel = self.bot.get_channel(c)
                    await log_channel.send(f"[{unvoter_name} unvoted.]({resp.jump_url})")

                logger.info(f"{unvoter_name} unvoted")

    """ 
    /player
    Displays information about a specific player.
    """
    @discord.slash_command(
        name="player",
        guild_ids=config.GUILD_IDS,
        description="Displays information about a specific player."
    )
    async def check_player(self, ctx: discord.ApplicationContext, player_name: str):
        player: dict = db.get_player(player_name)
        if player == None:
            await ctx.respond(f"Player \'{player_name}\' does not exist. Please check your spelling and try again.")
            return
        return_msg: str = f"```ini\n[Player Name: {player.get("name")}]\n"
        voters = ""
        vl = len(player.get("votes"))
        if vl > 0:
            for i in range(vl - 1):
                voters += player.get("votes")[i] + ", "
            voters += player.get("votes")[vl - 1]
        return_msg += f"[Votes ({player.get("number_of_votes")}): {voters}]\n"
        return_msg += f"[Currently voting for: {player.get("voted_for")}]```"
        await ctx.respond(return_msg)
        
        

def setup(bot: discord.Bot): # this is called by Pycord to setup the cog
    bot.add_cog(PlayerCommands(bot)) # add the cog to the bot