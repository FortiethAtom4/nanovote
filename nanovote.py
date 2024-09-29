import os
import logging
import discord
from discord.ext import commands
from dotenv import load_dotenv

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



# to show when bot first logs in.
@bot.event
async def on_ready():
    print(f'''Successfully logged in as {bot.user}.
Current latency: {round(bot.latency*1000,3)}ms''')


# commands here
@bot.slash_command(
    name="addplayer",
    guild_ids=[GUILD_ID],
    description="ADMIN: Adds a player to a Mafia game."
)
@commands.has_permissions(administrator=True)
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
    response_string = "```ini\n[Votes:]\n"

    if len(players) == 0:
        await ctx.respond("No players have been added yet.")
        return
    
    for player in players:
        response_string += player.to_string(False)+"\n"
    response_string += "```"
    await ctx.respond(response_string)

@bot.slash_command(
    name="playerinfo",
    guild_ids=[GUILD_ID],
    description="ADMIN: displays all info about current players."
)
@commands.has_permissions(administrator=True)
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
        username = ctx.user.name
        if not db.is_playing(username):
            await ctx.respond("You are not alive in this game!")
            return

        match(db.vote(username,voted_for_name)):
            case -1:
                await ctx.respond(f"You have already voted!")
            case 2:
                await ctx.respond(f"Player \'{voted_for_name}\' does not exist. Please check your spelling and try again.")
            case 1:
                await ctx.respond(f"There was an unexpected error when processing vote for {voted_for_name}. Please try again.")
            case 0:
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
                await ctx.respond("You unvoted.")
    else:
        await ctx.respond("Mafia commands are not allowed in this channel. Please ask an admin to use /setchannel or use the appropriate channels.")

@bot.slash_command(
    name="kill",
    guild_ids=[GUILD_ID],
    description="ADMIN: Kills a player."
)
@commands.has_permissions(administrator=True)
async def kill(ctx: discord.ApplicationContext, player_name: str):
    match db.kill_player(player_name):
        case 1:
            await ctx.respond("There was an unexpected error when processing the kill. Please try again.",ephemeral=True)

        case 0:
            await ctx.respond(f"{player_name} has been killed. Remember to announce the death in daytime chat.",ephemeral=True)

        
@bot.slash_command(
    name="resetvotes",
    guild_ids=[GUILD_ID],
    description="ADMIN: Reset all votes."
)
@commands.has_permissions(administrator=True)
async def end_day(ctx: discord.ApplicationContext):
    match db.end_day():
        case 0:
            await ctx.respond("All votes have been reset.",ephemeral=True)

        case 1:
            await ctx.respond("There was an unexpected error resetting votes. Please try again.",ephemeral=True)

@bot.slash_command(
    name="setvotevalue",
    guild_ids=[GUILD_ID],
    description="ADMIN: Set the value of a player's votes."
)
@commands.has_permissions(administrator=True)
async def set_vote_value(ctx: discord.ApplicationContext, player_name: str, value: int):
    match db.set_vote_value(player_name,value):
        case 1:
            await ctx.respond("There was an unexpected error setting vote value. Please try again.",ephemeral=True)
        case -1:
            await ctx.respond(f"Player {player_name} does not exist. Please check your spelling and try again.",ephemeral=True)
        case 0:
            await ctx.respond(f"{player_name}'s vote value has been set to {value}. NOTE: use /playerinfo to see players' vote values.",ephemeral=True)



@bot.slash_command(
    name="setchannel",
    guild_ids=[GUILD_ID],
    description="ADMIN: adds the current channel to the list of valid voting channels."
)
@commands.has_permissions(administrator=True)
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
    description="ADMIN: Removes the current channel from the list of valid voting channels."
)
@commands.has_permissions(administrator=True)
async def remove_channel(ctx: discord.ApplicationContext):
    db.remove_channel(int(ctx.channel.id))
    await ctx.respond("Voting commands are no longer accessible from this channel.")


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