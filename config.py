import datetime, dotenv, os

# global time variables
cur_time = datetime.datetime.now()
end_time = datetime.datetime.now()
timer_on: bool = False
mod_to_dm: str = "" #sends a message to player who sets the timer
majority: bool = False # for when majority is reached

# To prevent spam, just going to be implemented in votecount for now
command_delay_timer: datetime.timedelta = datetime.datetime.now()
command_delay_seconds: int = 10 # Total seconds to delay

# local lists of channel ids. Fetched when the bot starts.
valid_channel_ids: list[int] = []
log_channel_ids: list[int] = []

# my test server ID
# dev_guild_id = 825590571606999040

# mafia server ID
# mafia_guild_id = 911178268332404756

# db env
dotenv.load_dotenv(dotenv.find_dotenv(usecwd=True))
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = int(os.getenv('GUILD_ID'))