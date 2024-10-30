import datetime, dotenv, os
from mafia import Player

# global time variables
cur_time = datetime.datetime.now()
end_time = datetime.datetime.now()
timer_on: bool = False
mod_to_dm: str = "" #sends a message to player who sets the timer
majority: bool = False # for when majority is reached

cogs: list[str] = [
    "player_commands",
    "mod_commands",
    "custom_commands"
]

# To prevent spam, just going to be implemented in votecount for now
command_delay_timer: datetime.timedelta = datetime.datetime.now()
command_delay_seconds: int = 10 # Total seconds to delay

# local lists of channel ids. Fetched when the bot starts.
valid_channel_ids: list[int] = []
log_channel_ids: list[int] = []

# player list fetched at bot start
players: list[Player] = []

# db env
dotenv.load_dotenv(dotenv.find_dotenv(usecwd=True))
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = int(os.getenv('GUILD_ID'))
USER = os.getenv("MONGODB_USER")
PASS = os.getenv("MONGODB_PASS")
CHANNEL_COLLECTION = os.getenv("DB_CHANNEL_COLLECTION")

# different db collections, one for dev env one for mafiacord
COLLECTION = os.getenv("DB_COLLECTION")
db_URL = f"mongodb+srv://{USER}:{PASS}@nanobot.lab1zmc.mongodb.net/"