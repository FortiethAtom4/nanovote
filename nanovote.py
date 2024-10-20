import discord
from discord.ext import commands
import datetime
from asyncio import sleep

# local imports
import db, config

intents = discord.Intents.all() 
bot = commands.Bot(intents=intents)
bot.load_extensions("cogs.player_commands","cogs.mod_commands")

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

"""
/shutdown
Allows the bot owner to force a bot shutdown remotely.
"""
@bot.slash_command(
    name="shutdown",
    guild_ids=[config.GUILD_ID],
    description="BOT OWNER: Shuts the bot down."
)
@commands.is_owner()
async def shutdown(ctx: discord.ApplicationContext):
    await ctx.respond("東雲の家は今日も平和であった。")
    await ctx.bot.close()
    exit()

bot.loop.create_task(do_timer())
# run the bot
bot.run(config.TOKEN)