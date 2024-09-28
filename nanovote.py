import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

# local imports
import db

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
intents = discord.Intents.all() 

# my test server ID
dev_guild_id = 825590571606999040

# mafia server ID
mafia_guild_id = 911178268332404756

bot = commands.Bot(intents=intents)

# to show when bot first logs in.
@bot.event
async def on_ready():
    print(f'''Successfully logged in as {bot.user}.
Current latency: {round(bot.latency*1000,3)}ms''')

# local variables
number_of_votecounts = 0

# commands here
@bot.slash_command(
    name="addplayer",
    guild_ids=[dev_guild_id],
    description="Adds a player to a Mafia game."
)
@commands.has_permissions(administrator=True)
async def start_game(ctx: discord.ApplicationContext, player_name: str, player_discord_username: str, faction: str):
    
    real_users = (member.name for member in ctx.bot.get_all_members())
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

    await ctx.respond(return_message)
    return

@bot.slash_command(
    name="votecount",
    guild_ids=[dev_guild_id],
    description="Gets all players in the game and their vote counts."
)
async def vote_count(ctx: discord.ApplicationContext):
    players = db.get_all_players()
    response_string = ""

    if len(players) == 0:
        await ctx.respond("No players have been added yet.")
        return
    
    for player in players:
        response_string += player.to_string()+"\n"
    await ctx.respond(response_string)

@bot.slash_command(
    name="vote",
    guild_ids=[dev_guild_id],
    description="Vote for a player to be lynched."
)
async def vote(ctx: discord.ApplicationContext, voted_for_name: str):
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


@bot.slash_command(
    name="unvote",
    guild_ids=[dev_guild_id],
    description="Revoke your vote on a player."
)
async def unvote(ctx: discord.ApplicationContext):
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

@bot.slash_command(
    name="kill",
    guild_ids=[dev_guild_id],
    description="Kills a player. Admin only."
)
@commands.has_permissions(administrator=True)
async def kill(ctx: discord.ApplicationContext, player_name: str):
    match db.kill_player(player_name):
        case 1:
            await ctx.respond("There was an unexpected error when processing the kill. Please try again.")

        case 0:
            await ctx.respond(f"{player_name} has died.")

        
@bot.slash_command(
    name="endday",
    guild_ids=[dev_guild_id],
    description="End the day. Admin only."
)
@commands.has_permissions(administrator=True)
async def end_day(ctx: discord.ApplicationContext):
    match db.end_day():
        case 0:
            await ctx.respond("The day has ended. All votes have been reset.")

        case 1:
            await ctx.respond("There was an unexpected error ending the day. Please try again.")


@bot.slash_command(
    name="shutdown",
    guild_ids=[dev_guild_id],
    description="Shuts the bot down. Owner-only."
)
@commands.is_owner()
async def shutdown(ctx: discord.ApplicationContext):
    await ctx.respond("Shutting down...")
    exit()

# run the bot
bot.run(TOKEN)