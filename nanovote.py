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

# To prevent spam, just going to be implemented in votecount for now
command_delay_timer: datetime.timedelta = datetime.datetime.now()
command_delay_seconds: int = 10 # Total seconds to delay

# local lists of channel ids. Fetched when the bot starts.
valid_channel_ids: list[int] = []
log_channel_ids: list[int] = []


# why did i waste my time adding this
print("""---------##---------
-------######-------
-----##########-----
---##############---
-##################-
##### NANOVOTE #####
-##################-
---##############---
-----##########-----
-------######-------
---------##---------\n""")
print("-> Logging in...")

# to show when bot first logs in.
@bot.event
async def on_ready():
    print(f"-+ Successfully logged in as {bot.user}.")
    print(f"-i Current latency: {round(bot.latency*1000,3)}ms")
    print("-> Retrieving voting channels...")
    global valid_channel_ids
    valid_channel_ids = db.get_all_valid_channels()
    print("-> Retrieving logging channels...")
    global log_channel_ids
    log_channel_ids = db.get_all_logging_channels()
    print("-+ Ready\n")
# checks and updates the time. Used for keeping track of day/night time
@bot.event
async def do_timer():
    global cur_time
    global end_time
    global timer_on
    while True:
        if timer_on:
            cur_time = datetime.datetime.now()
            if cur_time >= end_time:
                global time_set_player
                if time_set_player != "":
                    user = await bot.fetch_user(time_set_player)
                    await user.send("Your timer is up!")
                timer_on = False
        await sleep(1)
    

bot.loop.create_task(do_timer())

""" 
/settimer
Sets a timer for the mod for the day to end.
Takes an integer value for number of hours.
Optional minutes variable as well for partial hours.
"""
@bot.slash_command(
    name="settimer",
    guild_ids=[GUILD_ID],
    description="MOD: Sets a timer for the day to end."
)
@commands.has_any_role("Moderator","Main Moderator")
async def set_timer(ctx: discord.ApplicationContext, time_hours: int, time_minutes: int = 0):
    global cur_time
    cur_time = datetime.datetime.now()
    tmp = cur_time + datetime.timedelta(hours=time_hours, minutes=time_minutes)
    
    global end_time
    end_time = tmp
    
    global timer_on
    timer_on = True

    global time_set_player
    time_set_player = ctx.interaction.user.id

    tmp_format_time = datetime.timedelta(seconds=int((end_time - cur_time).total_seconds()))
    print(f"-+ Timer set to {tmp_format_time} by {bot.get_user(time_set_player)}")
    await ctx.respond(f"Timer has been set to **{tmp_format_time}**, starting now. You will be sent a DM when time is up or if a majority is reached.")

'''
/togglemajority
'''
@bot.slash_command(
    name="togglemajority",
    guild_ids=[GUILD_ID],
    description="MOD: toggles majority check."
)
@commands.has_any_role("Moderator","Main Moderator")
async def toggle_majority(ctx: discord.Interaction):
    global majority, timer_on, time_set_player
    majority = not majority
    if not timer_on:
        timer_on = True
    await ctx.respond(f"Majority flag set to `{majority}`.",ephemeral=True)

@bot.slash_command(
    name="toggletimer",
    guild_ids=[GUILD_ID],
    description="MOD: Manually starts/stops the timer. Stopping the timer will display 'time is up' to your players."
)
@commands.has_any_role("Moderator","Main Moderator")
async def toggle_timer(ctx: discord.Interaction):
    global timer_on, end_time, cur_time
    if end_time <= cur_time:
        await ctx.respond("Timer cannot be toggled as no time has been set. Use /settimer first.")
        return
    temp_timer_time = end_time-cur_time
    timer_on = not timer_on
    if timer_on:
        cur_time = datetime.datetime.now()
        end_time = cur_time + temp_timer_time
    await ctx.respond(f"Timer {("started" if timer_on else "stopped")}.",ephemeral=True)

""" 
/checktime
Sends a message stating the time left on the bot's timer.
Checktime messages are private so as not to spam the chat with timers.
If time needs to be seen publicly, use /votecount.
"""
@bot.slash_command(
    name="checktime",
    guild_ids=[GUILD_ID],
    description="Gets the amount of time left."
)
async def check_time(ctx: discord.Interaction):
    global timer_on
    if not timer_on:
        await ctx.respond("Timer has not been set.",ephemeral=True)
        return
    global cur_time
    global end_time
    tmp_format_time = datetime.timedelta(seconds=int((end_time - cur_time).total_seconds()))
    await ctx.respond(f"Time remaining: **{tmp_format_time}**",ephemeral=True)


"""
/addtime
Adds extra time to the timer.
Works with negative values.
"""
@bot.slash_command(
    name="addtime",
    guild_ids=[GUILD_ID],
    description="MOD: Adds time to the timer. Negative values will subtract time instead."
)
@commands.has_any_role("Moderator","Main Moderator")
async def set_timer(ctx: discord.Interaction, time_hours: int, time_minutes: int = 0):
    global timer_on
    if not timer_on:
        await ctx.respond("Timer has not been set. Set it first with /settimer.")
        return
    
    global end_time
    total_seconds = time_hours * 3600 + time_minutes * 60
    time_to_add = datetime.timedelta(seconds=total_seconds)
    end_time += time_to_add

    print(f"-+ Added {total_seconds} seconds to the timer")
    if total_seconds < 0:
        await ctx.respond(f"{datetime.timedelta(seconds=-total_seconds)} subtracted.")
    else:
        await ctx.respond(f"{time_to_add} added.")

"""
/addplayer
Persists a new Player object to the database.
Includes name, Discord username, and their faction.
"""
@bot.slash_command(
    name="addplayer",
    guild_ids=[GUILD_ID],
    description="MOD: Adds a player to a Mafia game."
)
@commands.has_any_role("Moderator","Main Moderator")
async def add_player(ctx: discord.Interaction, player_name: str, player_discord_username: str, faction: str):
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
    return

""" 
/votecount
Retrieves a list of all players in the game and their vote counts.
Also displays the number of votes needed for majority and remaining time.
"""
@bot.slash_command(
    name="votecount",
    guild_ids=[GUILD_ID],
    description="Gets all players in the game and their vote counts."
)
async def vote_count(ctx: discord.Interaction):
    global command_delay_timer
    time_rem: datetime.timedelta = command_delay_timer - datetime.datetime.now()
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

    global majority
    global timer_on
    if majority:
        timer_on = False
        response_string += "\n[A majority has been reached.]\n"
    else:
        response_string += f"\n[With {len(players)} players, it takes {majority_value} votes to reach majority.]\n"

    global end_time, cur_time
    tmp_format_time = datetime.timedelta(seconds=int((end_time - cur_time).total_seconds()))
    if timer_on:
        response_string += f"[{(f"Time remaining: {tmp_format_time}" if tmp_format_time > datetime.timedelta(seconds=0) else "Time is up!")}]\n"
    else:
        response_string += f"[Time remaining when majority was reached: {(tmp_format_time if tmp_format_time > datetime.timedelta(seconds=0) else datetime.timedelta(seconds=0))}]\n" if majority else "[Time is up!]\n"
    response_string += "```"
    print("-+ Sent votecount")
    await initial_response.edit(content=response_string)
    # increment anti-spam timer
    global command_delay_seconds
    command_delay_timer = datetime.datetime.now() + datetime.timedelta(seconds=command_delay_seconds)

""" 
/playerinfo
An advanced form of /votecount that shows additional info about each player.
This includes who each player has voted for, their vote's value, and their faction.
Response is invisible to other players to avoid accidental info leaks.
"""
@bot.slash_command(
    name="playerinfo",
    guild_ids=[GUILD_ID],
    description="MOD: displays all info about current players."
)
@commands.has_any_role("Moderator","Main Moderator")
async def player_info(ctx: discord.Interaction):
    initial_response = await ctx.respond("Getting the deets...",ephemeral=True)
    print("-> Getting all player info...")
    players = db.get_all_players()
    response_string = "```"
    for player in players:
        response_string += player.to_string(True)
        response_string += "\n-----\n"
    response_string += "```"
    print("-+ Sent player info")
    await initial_response.edit(content=response_string)

""" 
/vote
Vote for a player to be lynched.
Votes will be logged in a configured log channel.
Will display a special message and disable voting commands if a majority is reached.
"""
@bot.slash_command(
    name="vote",
    guild_ids=[GUILD_ID],
    description="Vote for a player to be lynched."
)
async def vote(ctx: discord.Interaction, voted_for_name: str):

    global valid_channel_ids
    if ctx.channel.id in valid_channel_ids:
        global majority
        if majority:
            await ctx.respond("Majority has been reached. Voting commands have been disabled.")
            print("-i Majority reached, voting commands have been disabled")
            return
        
        global timer_on
        if not timer_on:
            await ctx.respond("Time is up. Voting commands have been disabled.")
            print("-i Time is up, voting commands have been disabled")
            return
        
        username = ctx.user.name
        if not db.is_playing(username):
            await ctx.respond("You are not alive in this game!")
            print(f"-i Non-participating player {ctx.user.name} cannot vote")
            return
        
        initial_response = await ctx.respond("Sending your vote in...")
        global log_channel_ids
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
                timer_on = False
                majority = True
                await initial_response.edit(content=f"You voted for {voted_for_name}. **MAJORITY REACHED**")
                global time_set_player
                mod = await bot.fetch_user(time_set_player)
                await mod.send("A majority has been reached!")
                resp: discord.Message = await initial_response.original_response()
                for c in log_channel_ids:
                    log_channel: discord.TextChannel = bot.get_channel(c)
                    await log_channel.send(f"[(LINK TO MESSAGE)]({resp.jump_url}) {voter_name} voted for {voted_for_name}. **MAJORITY REACHED**")
                print(f"-+ {voter_name} voted for {voted_for_name} and a majority was reached")
            case 0:
                await initial_response.edit(content=f"You voted for {voted_for_name}.")
                resp: discord.Message = await initial_response.original_response()
                for c in log_channel_ids:
                    log_channel: discord.TextChannel = bot.get_channel(c)
                    await log_channel.send(f"[(LINK TO MESSAGE)]({resp.jump_url}) {voter_name} voted for {voted_for_name}.")
                print(f"-+ {voter_name} voted for {voted_for_name}")
    else:
        await ctx.respond(content="Mafia commands are not allowed in this channel. Please ask an admin to use /setchannel or use the appropriate channels.")
        print("-i Vote sent in from a channel not flagged for voting commands, ignoring")

""" 
/unvote
Revokes a player's vote.
Unvotes will be logged in a configured log channel.
"""
@bot.slash_command(
    name="unvote",
    guild_ids=[GUILD_ID],
    description="Revoke your vote on a player."
)
async def unvote(ctx: discord.Interaction):
    global valid_channel_ids
    if ctx.channel.id in valid_channel_ids:
        global majority
        if majority:
            await ctx.respond("Majority has been reached. Voting commands have been disabled.")
            print("-i Majority reached, voting commands have been disabled")
            return
        
        global timer_on
        if not timer_on:
            await ctx.respond("Time is up. Voting commands have been disabled.")
            print("-i Time is up, voting commands have been disabled")
            return
        
        username = ctx.user.name
        if not db.is_playing(username):
            await ctx.respond("You are not alive in this game!")
            print(f"-i Non-participating player {ctx.user.name} cannot unvote")
            return 
        
        initial_response = await ctx.respond("Pretending to do work...")
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
                global log_channel_ids
                resp: discord.Message = await initial_response.original_response()
                for c in log_channel_ids:
                    log_channel: discord.TextChannel = bot.get_channel(c)
                    await log_channel.send(f"[(LINK TO MESSAGE)]({resp.jump_url}) {unvoter_name} unvoted.")

                print(f"-+ {unvoter_name} unvoted")
    else:
        await ctx.respond("Mafia commands are not allowed in this channel. Please ask an admin to use /setchannel or use the appropriate channels.")
        print("-i Unvote sent in from a channel not flagged for voting commands, ignoring")

"""
/kill
Kills a player.
Removes all their votes and resets all votes on that player.
"""
@bot.slash_command(
    name="kill",
    guild_ids=[GUILD_ID],
    description="MOD: Kills a player."
)
@commands.has_any_role("Moderator","Main Moderator")
async def kill(ctx: discord.Interaction, player_name: str):
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
@bot.slash_command(
    name="resetvotes",
    guild_ids=[GUILD_ID],
    description="MOD: Reset all votes."
)
@commands.has_any_role("Moderator","Main Moderator")
async def end_day(ctx: discord.Interaction):

    print("-> Resetting all votes...")
    match db.end_day():
        case 0:
            print("-+ All votes reset")
            global majority
            majority = False
            await ctx.respond("All votes have been reset.",ephemeral=True)

        case 1:
            print("-- An error occurred when resetting votes")
            await ctx.respond("There was an unexpected error resetting votes. Please try again.",ephemeral=True)

"""
/setvotevalue
Sets the value of a player's votes.
Functions for both positive and negative values.
"""
@bot.slash_command(
    name="setvotevalue",
    guild_ids=[GUILD_ID],
    description="MOD: Set the value of a player's votes."
)
@commands.has_any_role("Moderator","Main Moderator")
async def set_vote_value(ctx: discord.Interaction, player_name: str, value: int):
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
@bot.slash_command(
    name="addvotes",
    guild_ids=[GUILD_ID],
    description="MOD: add or subtract votes from a player."
)
@commands.has_any_role("Moderator","Main Moderator")
async def add_votes(ctx: discord.Interaction, player_name: str, value: int):
    print(f"-> Adding {value} vote{"s" if value is not abs(1) else ""} to {player_name}...")
    match db.mod_add_vote(player_name,value):
        case 1:
            print(f"-- An unexpected error occurred when adding votes")
            await ctx.respond("Unexpected error, please try again",ephemeral=True)
        case -1:
            print(f"-i Player {player_name} not found, aborting")
            await ctx.respond(f"Player {player_name} does not exist. Please check your spelling and try again.",ephemeral=True)
        case 1000:
            global majority
            majority = True
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
@bot.slash_command(
    name="setchannel",
    guild_ids=[GUILD_ID],
    description="MOD: adds the current channel to the list of valid voting channels."
)
@commands.has_any_role("Moderator","Main Moderator")
async def set_channel(ctx: discord.Interaction):
    global valid_channel_ids
    to_set = ctx.channel.id
    if to_set in valid_channel_ids:
        await ctx.respond("This channel is already set. Remove it with /removechannel.")
        print("-i Channel already set")
        return
    valid_channel_ids.append(ctx.channel.id)
    await ctx.respond(f"Channel set. Voting commands are now accessible from this channel.")
    print("-> Persisting new voting channel to database...")
    db.persist_voting_channel(int(to_set))
    print("-+ Channel added")

"""
/removechannel
Removes a channel from the 'channels' collection, disallowing voting or logs in it.
"""
@bot.slash_command(
    name="removechannel",
    guild_ids=[GUILD_ID],
    description="MOD: Removes the current channel from the list of valid voting channels."
)
@commands.has_any_role("Moderator","Main Moderator")
async def remove_channel(ctx: discord.Interaction):
    global valid_channel_ids
    to_remove = int(ctx.channel.id)
    if to_remove not in valid_channel_ids:
        await ctx.respond("This channel has not been set for voting.")
        print("-i Channel has not been set for voting, skipping")
        return
    valid_channel_ids.remove(to_remove)
    await ctx.respond("Voting commands are no longer accessible from this channel.")
    print("-> Removing channel from database...")
    db.remove_channel(int(ctx.channel.id))
    print("-+ Channel removed")


"""
/setlogchannel
Flags a channel to log voting and unvoting.
Only one log channel can be set at a time.
"""
@bot.slash_command(
    name="setlogchannel",
    guild_ids=[GUILD_ID],
    description="MOD: flags the current channel for logging voting events."
)
@commands.has_any_role("Moderator","Main Moderator")
async def set_log_channel(ctx: discord.Interaction):
    cur_channel = int(ctx.channel.id)
    global log_channel_ids
    if cur_channel in log_channel_ids:
        await ctx.respond("This channel is already set for logging. Remove it with /removelogchannel.")
        print("-i Channel already set")
        return

    log_channel_ids.append(cur_channel)
    await ctx.respond("This channel has been flagged for logging events. Remove this flag with /removelogchannel.")
    print("-> Persisting logging channel to database...")
    db.persist_logging_channel(cur_channel)
    print("-+ Channel added")

"""
/removelogchannel
Deletes the flagged channel ID, disabling logging for it.
"""
@bot.slash_command(
    name="removelogchannel",
    guild_ids=[GUILD_ID],
    description="MOD: removes flag from the configured logging channel."
)
@commands.has_any_role("Moderator","Main Moderator")
async def remove_log_channel(ctx: discord.Interaction):
    global log_channel_ids
    to_remove = int(ctx.channel.id)
    if to_remove not in log_channel_ids:
        await ctx.respond("This channel does not have a logging flag to remove.")
        print("-i Log channel not set, skipping")
        return
    log_channel_ids.remove(to_remove)
    await ctx.respond("Logging flag removed.")
    print("-> Removing logging channel from database...")
    db.remove_channel(int(ctx.channel.id))
    print("-+ Channel removed")

"""
/shutdown
Allows the bot owner to force a bot shutdown remotely.
"""
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