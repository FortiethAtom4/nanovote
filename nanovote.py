import os
import logging
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import datetime
from asyncio import sleep

# local imports
import db

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = os.getenv('GUILD_ID')
intents = discord.Intents.all() 

# my test server ID
# dev_guild_id = 825590571606999040

# mafia server ID
# mafia_guild_id = 911178268332404756

bot = commands.Bot(intents=intents)

# logger = logging.getLogger('discord')
# logger.setLevel(logging.DEBUG)
# handler = logging.FileHandler(filename='nanovote.log', encoding='utf-8', mode='w')
# handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
# logger.addHandler(handler)

# global time variables
cur_time = datetime.datetime.now()
end_time = datetime.datetime.now()
timer_on: bool = False
time_set_player = "" #sends a message to player who sets the timer
majority: bool = False # for when majority is reached

log_channel_id = -1 #for logging vote events

# to show when bot first logs in.
# checks and updates the time. Used for keeping track of day/night time
@bot.event
async def check_time():
    await bot.wait_until_ready()
    print(f'''Successfully logged in as {bot.user}.
Current latency: {round(bot.latency*1000,3)}ms''')
    while True:
        global cur_time
        cur_time = datetime.datetime.now()

        global end_time
        global timer_on
        if timer_on and cur_time >= end_time:
            global time_set_player
            user = await bot.fetch_user(time_set_player)
            await user.send("Your timer is up!")
            timer_on = False
        await sleep(1)

bot.loop.create_task(check_time())

@bot.slash_command(
    name="settimer",
    guild_ids=[GUILD_ID],
    description="MOD: Sets a timer for the day to end. Time measured in hours."
)
@commands.has_any_role("Moderator","Main Moderator")
async def set_timer(ctx: discord.ApplicationContext, time_hours: int, time_minutes: int = 0):
    tmp = datetime.datetime.now() + datetime.timedelta(hours=time_hours, minutes=time_minutes)
    
    global end_time
    end_time = tmp
    
    global timer_on
    timer_on = True

    global time_set_player
    time_set_player = ctx.interaction.user.id
    await ctx.respond(f"Timer has been set for {tmp.replace(microsecond=0)} EST. You will be sent a DM when time is up.")

@bot.slash_command(
    name="checktime",
    guild_ids=[GUILD_ID],
    description="Gets the amount of time left."
)
async def check_time(ctx: discord.ApplicationContext):
    global timer_on
    if not timer_on:
        await ctx.respond("Timer has not been set.",ephemeral=True)
        return
    global cur_time
    global end_time
    tmp_format_time = datetime.timedelta(seconds=int((end_time - cur_time).total_seconds()))
    await ctx.respond(f"Time remaining: **{tmp_format_time}**",ephemeral=True)

# commands here
@bot.slash_command(
    name="addplayer",
    guild_ids=[GUILD_ID],
    description="MOD: Adds a player to a Mafia game."
)
@commands.has_any_role("Moderator","Main Moderator")
async def add_player(ctx: discord.ApplicationContext, player_name: str, player_discord_username: str, faction: str):
    real_users = [member.name for member in ctx.bot.get_all_members()]
    if player_discord_username not in real_users:
        await ctx.respond("That username does not exist. Please check your spelling and try again.")
        return
    
    return_message = ""
    match db.add_player(player_name, player_discord_username, faction):
        case 0:
            return_message = f"Player {player_name} ({player_discord_username}) successfully added."
        case 1:
            return_message = f"There was a problem adding this player. Please try again."
        case -1:
            return_message = f"Player {player_name} ({player_discord_username}) is already in the game."

    await ctx.respond(return_message,ephemeral=True)
    return

@bot.slash_command(
    name="votecount",
    guild_ids=[GUILD_ID],
    description="Gets all players in the game and their vote counts."
)
async def vote_count(ctx: discord.ApplicationContext):
    players = db.get_all_players()
    

    if len(players) == 0:
        await ctx.respond("No players have been added yet.")
        return
    
    response_string = "```ini\n[Votes:]\n"

    for player in players:
        response_string += player.to_string(False)+"\n"

    global end_time, cur_time, timer_on
    if timer_on:
        tmp_format_time = datetime.timedelta(seconds=int((end_time - cur_time).total_seconds()))
        response_string += f"\n[Time remaining: {tmp_format_time}]\n"
    else:
        response_string += "\n[Time is up!]\n"
    response_string += "```"
    await ctx.respond(response_string)

@bot.slash_command(
    name="playerinfo",
    guild_ids=[GUILD_ID],
    description="MOD: displays all info about current players."
)
@commands.has_any_role("Moderator","Main Moderator")
async def player_info(ctx: discord.ApplicationContext,invisible: bool):
    players = db.get_all_players()
    response_string = ""
    for player in players:
        response_string += player.to_string(True)
        response_string += "\n-----\n"
    await ctx.respond(response_string,ephemeral=invisible)

@bot.slash_command(
    name="vote",
    guild_ids=[GUILD_ID],
    description="Vote for a player to be lynched."
)
async def vote(ctx: discord.ApplicationContext, voted_for_name: str):
    if db.is_valid_channel(int(ctx.channel.id)):
        global majority
        if majority:
            await ctx.respond("Majority has been reached. Voting commands have been disabled.")
            return
        
        global timer_on
        if not timer_on:
            await ctx.respond("Time is up. Voting commands have been disabled.")
            return
        
        username = ctx.user.name
        if not db.is_playing(username):
            await ctx.respond("You are not alive in this game!")
            return
        global log_channel_id
        match(db.vote(username,voted_for_name)):
            case -1:
                await ctx.respond(f"You have already voted!")
            case 2:
                await ctx.respond(f"Player \'{voted_for_name}\' does not exist. Please check your spelling and try again.")
            case 1:
                await ctx.respond(f"There was an unexpected error when processing vote for {voted_for_name}. Please try again.")
            case 1000:
                majority = True
                await ctx.respond(f"You voted for {voted_for_name}. **MAJORITY REACHED**")
                if log_channel_id != -1:
                    log_channel = bot.get_channel(log_channel_id)
                    await log_channel.send(f"{db.get_name_from_username(username)} voted for {voted_for_name}. **MAJORITY REACHED**")
            case 0:
                if log_channel_id != -1:
                    log_channel = bot.get_channel(log_channel_id)
                    await log_channel.send(f"{db.get_name_from_username(username)} voted for {voted_for_name}.")
                await ctx.respond(f"You voted for {voted_for_name}.")
    else:
        await ctx.respond("Mafia commands are not allowed in this channel. Please ask an admin to use /setchannel or use the appropriate channels.")


@bot.slash_command(
    name="unvote",
    guild_ids=[GUILD_ID],
    description="Revoke your vote on a player."
)
async def unvote(ctx: discord.ApplicationContext):
    if db.is_valid_channel(int(ctx.channel.id)):
        global majority
        if majority:
            await ctx.respond("Majority has been reached. Voting commands have been disabled.")
            return
        
        global timer_on
        if not timer_on:
            await ctx.respond("Time is up. Voting commands have been disabled.")
            return
        
        username = ctx.user.name
        if not db.is_playing(username):
            await ctx.respond("You are not alive in this game!")
            return 
        
        match(db.unvote(username)):
            case 1:
                await ctx.respond("There was an unexpected error when processing your unvote. Please try again.")
            case -1:
                await ctx.respond("You haven't voted for anyone yet.")
            case 0:
                global log_channel_id
                if log_channel_id != -1:
                    log_channel = bot.get_channel(log_channel_id)
                    await log_channel.send(f"{db.get_name_from_username(username)} unvoted.")
                await ctx.respond("You unvoted.")
    else:
        await ctx.respond("Mafia commands are not allowed in this channel. Please ask an admin to use /setchannel or use the appropriate channels.")

@bot.slash_command(
    name="kill",
    guild_ids=[GUILD_ID],
    description="MOD: Kills a player."
)
@commands.has_any_role("Moderator","Main Moderator")
async def kill(ctx: discord.ApplicationContext, player_name: str):
    match db.kill_player(player_name):
        case 1:
            await ctx.respond("There was an unexpected error when processing the kill. Please try again.",ephemeral=True)

        case 0:
            await ctx.respond(f"{player_name} has been killed. Remember to announce the death in daytime chat.",ephemeral=True)

        
@bot.slash_command(
    name="resetvotes",
    guild_ids=[GUILD_ID],
    description="MOD: Reset all votes."
)
@commands.has_any_role("Moderator","Main Moderator")
async def end_day(ctx: discord.ApplicationContext):
    match db.end_day():
        case 0:
            global majority
            majority = False
            await ctx.respond("All votes have been reset.",ephemeral=True)

        case 1:
            await ctx.respond("There was an unexpected error resetting votes. Please try again.",ephemeral=True)

@bot.slash_command(
    name="setvotevalue",
    guild_ids=[GUILD_ID],
    description="MOD: Set the value of a player's votes."
)
@commands.has_any_role("Moderator","Main Moderator")
async def set_vote_value(ctx: discord.ApplicationContext, player_name: str, value: int):
    match db.set_vote_value(player_name,value):
        case 1:
            await ctx.respond("There was an unexpected error setting vote value. Please try again.",ephemeral=True)
        case -1:
            await ctx.respond(f"Player {player_name} does not exist. Please check your spelling and try again.",ephemeral=True)
        case 0:
            await ctx.respond(f"{player_name}'s vote value has been set to {value}. NOTE: use /playerinfo to see players' vote values.",ephemeral=True)

@bot.slash_command(
    name="addvotes",
    guild_ids=[GUILD_ID],
    description="MOD: add or subtract votes from a player."
)
@commands.has_any_role("Moderator","Main Moderator")
async def add_votes(ctx: discord.ApplicationContext, player_name: str, value: int):
    match db.mod_add_vote(player_name,value):
        case 1:
            await ctx.respond("Unexpected error, please try again",ephemeral=True)
        case -1:
            await ctx.respond(f"Player {player_name} does not exist. Please check your spelling and try again.",ephemeral=True)
        case 1000:
            global majority
            majority = True
            await ctx.respond(f"Vote added to {player_name}. NOTE: A MAJORITY HAS BEEN REACHED. Voting has been disabled for your players.",ephemeral=True)
        case 0:
            await ctx.respond(f"Vote added to {player_name}.",ephemeral=True)

@bot.slash_command(
    name="setchannel",
    guild_ids=[GUILD_ID],
    description="MOD: adds the current channel to the list of valid voting channels."
)
@commands.has_any_role("Moderator","Main Moderator")
async def set_channel(ctx: discord.ApplicationContext):
    match db.set_channel(int(ctx.channel.id)):
        case -1:
            await ctx.respond("This channel is already set. Remove it with /removechannel.")
        case 1:
            await ctx.respond("An unexpected error occurred when setting the channel. Please try again.")
        case 0:
            await ctx.respond(f"Channel set. Voting commands are now accessible from this channel.")

@bot.slash_command(
    name="removechannel",
    guild_ids=[GUILD_ID],
    description="MOD: Removes the current channel from the list of valid voting channels."
)
@commands.has_any_role("Moderator","Main Moderator")
async def remove_channel(ctx: discord.ApplicationContext):
    db.remove_channel(int(ctx.channel.id))
    await ctx.respond("Voting commands are no longer accessible from this channel.")

@bot.slash_command(
    name="setlogchannel",
    guild_ids=[GUILD_ID],
    description="MOD: flags the current channel for logging voting events."
)
@commands.has_any_role("Moderator","Main Moderator")
async def set_log_channel(ctx: discord.ApplicationContext):
    global log_channel_id 
    log_channel_id = int(ctx.channel.id)
    await ctx.respond("This channel has been flagged for logging events. Remove this flag with /removelogchannel.")

@bot.slash_command(
    name="removelogchannel",
    guild_ids=[GUILD_ID],
    description="MOD: removes flag from the configured logging channel."
)
@commands.has_any_role("Moderator","Main Moderator")
async def remove_log_channel(ctx: discord.ApplicationContext):
    global log_channel_id
    log_channel_id = -1
    await ctx.respond("Logging flag removed.")



@bot.slash_command(
    name="shutdown",
    guild_ids=[GUILD_ID],
    description="BOT OWNER: Shuts the bot down."
)
@commands.is_owner()
async def shutdown(ctx: discord.ApplicationContext):
    await ctx.respond("Shutting down...")
    exit()

# run the bot
bot.run(TOKEN)