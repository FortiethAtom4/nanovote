import discord
from discord.ext import commands
import datetime
from asyncio import sleep

# local imports
import utils.db as db, config

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
    print(f"-+ {datetime.datetime.today()} Ready\n")
    
# checks and updates the time. Used for keeping track of day/night time
@bot.event
async def do_timer():
    while True:
        if not config.timer.stopped:
            if(config.timer.increment()):
                if config.mod_to_dm != "":
                    user = await bot.fetch_user(config.mod_to_dm)
                    await user.send("Your timer is up!")
                print("-> Timer expired, persisting updates...")
                db.persist_updates()
                print("-+ Updates persisted to database")
        await sleep(1)

# updates the database every 10 minutes
@bot.event
async def do_update():
    config.update_timer.start(datetime.timedelta(minutes=config.update_interval))
    while True:
        if config.update_timer.increment():
            print(f"-> {datetime.datetime.today()} Periodic update started...")
            db.persist_updates()
            print(f"-+ {datetime.datetime.today()} Updates completed.")
            config.update_timer.start(datetime.timedelta(minutes=config.update_interval))
        await sleep(1)

bot.loop.create_task(do_timer())
bot.loop.create_task(do_update())
# run the bot
bot.run(config.TOKEN)