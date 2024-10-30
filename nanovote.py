import discord
from discord.ext import commands
import datetime
from asyncio import sleep

# local imports
import db, config

intents = discord.Intents.all() 
bot = commands.Bot(intents=intents)
for cog in config.cogs:
    bot.load_extension(f"cogs.{cog}")


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
    config.valid_channel_ids = db.get_all_valid_channels()
    print("-> Retrieving logging channels...")
    config.log_channel_ids = db.get_all_logging_channels()
    print("-> Retrieving players...")
    config.players = db.get_all_players()
    print("-+ Ready\n")
    
# checks and updates the time. Used for keeping track of day/night time
@bot.event
async def do_timer():
    while True:
        if config.timer_on:
            config.cur_time = datetime.datetime.now()
            if config.cur_time >= config.end_time:
                if config.mod_to_dm != "":
                    user = await bot.fetch_user(config.mod_to_dm)
                    await user.send("Your timer is up!")
                config.timer_on = False
        await sleep(1)

# updates the database every 10 minutes
@bot.event
async def do_update():
    
    update_time: datetime.timedelta = datetime.datetime.now() + datetime.timedelta(minutes=config.update_interval)
    cur_update_time = datetime.datetime.now()
    while True:
        cur_update_time = datetime.datetime.now()
        if cur_update_time >= update_time:
            print(f"-> {datetime.datetime.today()} Persisting updates...")
            db.persist_updates()
            print(f"-+ {datetime.datetime.today()} Updates completed.")
            update_time = datetime.datetime.now() + datetime.timedelta(minutes=config.update_interval)
        await sleep(60)


"""
/shutdown
Allows the bot owner to force a bot shutdown remotely. Saves all mafia data before closing.
"""
@bot.slash_command(
    name="shutdown",
    guild_ids=[config.GUILD_ID],
    description="BOT OWNER: Shuts the bot down."
)
@commands.is_owner()
async def shutdown(ctx: discord.ApplicationContext):
    print("-> Updating...")
    db.persist_updates()
    print("-+ Update complete, shutting down")
    await ctx.respond("東雲の家は今日も平和であった。")
    await ctx.bot.close()
    exit()

bot.loop.create_task(do_timer())
bot.loop.create_task(do_update())
# run the bot
bot.run(config.TOKEN)