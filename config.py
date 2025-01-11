import datetime, dotenv, os, logging
from mafia import Player
from utils.timer import Timer

########## ADD YOUR COG FILE NAME TO THIS LIST ##########
cogs: list[str] = [
    "player_commands",
    "mod_commands",
    "custom_commands",
    "bot_admin_commands"
]
#################################################
# server_ids: list[int] = [
#     334031029352267776 #shrek server ID
# ]

mod_to_dm: str = None #sends a message to player who sets this value
majority: bool = False # for when majority is reached

timer: Timer = Timer() # Game timer

update_timer: Timer = Timer() # Timer used for automatic database updates
update_interval: int = 15 # number of minutes to wait between automatic updates

# To prevent spam, just going to be implemented in votecount for now
command_delay_timer: datetime.timedelta = datetime.datetime.now()
command_delay_seconds: int = 10 # Total seconds to delay

# local lists of channel ids. Fetched when the bot starts.
valid_channel_ids: list[int] = []
log_channel_ids: list[int] = []

# player list fetched at bot start
players: list[Player] = []

#config formatter
log_formatter = '%(asctime)s :: %(name)s :: %(levelname)s :: %(message)s'

# private variables from the .env
dotenv.load_dotenv(dotenv.find_dotenv(usecwd=True))
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_IDS: list[int] = [int(x) for x in (os.getenv('GUILD_IDS')).split(",")] #allows multiple guild IDs separated by comma
USER = os.getenv("MONGODB_USER")
PASS = os.getenv("MONGODB_PASS")
DB_NAME = os.getenv("DB_NAME")
COLLECTION = os.getenv("DB_COLLECTION")
CHANNEL_COLLECTION = os.getenv("DB_CHANNEL_COLLECTION")
MOD_ID = os.getenv("MOD_ID")
db_URL = f"mongodb+srv://{USER}:{PASS}@nanobot.lab1zmc.mongodb.net/"