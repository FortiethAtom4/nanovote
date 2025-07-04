import discord, logging, datetime
from discord.ext import commands, tasks
from discord.ext.commands.errors import MissingAnyRole
from asyncio import sleep

# local imports
import utils.db as db, config

logger = logging.getLogger(__name__)
logging.basicConfig(filename='mafia.log', encoding='utf-8', level=logging.INFO, format=config.log_formatter)

intents = discord.Intents.all() 
bot = commands.Bot(intents=intents)
for cog in config.cogs:
    bot.load_extension(f"cogs.{cog}")


# style points
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
logger.info("### Bot starting... ###")


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
    logger.info("Ready")
    
# checks and updates the time. Used for keeping track of day/night time
async def do_timer():
    while True:
        if not config.timer.stopped:
            if(config.timer.increment()):
                if config.mod_to_dm != None:
                    user = await bot.fetch_user(config.mod_to_dm)
                    await user.send("Your timer is up!")
                print("-> Timer expired, persisting updates...")
                db.persist_updates()
                print("-+ Updates persisted to database")
        await sleep(1)

# updates the database automatically at regular intervals
async def do_update():
    config.update_timer.start(datetime.timedelta(minutes=config.update_interval))
    while True:
        if config.update_timer.increment():
            print(f"-> {datetime.datetime.today()} Periodic database update started...")
            db.persist_updates()
            print(f"-+ {datetime.datetime.today()} Update completed.")
            config.update_timer.start(datetime.timedelta(minutes=config.update_interval))
        await sleep(1)



bot.loop.create_task(do_timer())
bot.loop.create_task(do_update())
# run the bot
bot.run(config.TOKEN)
