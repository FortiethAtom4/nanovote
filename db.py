import pymongo
import pymongo.collection
from math import trunc

# local imports
import config
from mafia import Player

# tests connection to database.
def test_connection():
    try:
        client = pymongo.MongoClient(config.db_URL)
        return client
    except:
        return -1
    
# fetches all valid channels
def get_all_valid_channels():
    try:
        client = pymongo.MongoClient(config.db_URL)
        db = client["MafiaPlayers"]
        channel = db[config.CHANNEL_COLLECTION]
        channel_list: list[dict] = channel.find({"type":"voting"}).to_list()
        to_return = []
        for c in channel_list:
            to_return.append(c.get("channel_id"))

        return to_return
    
    except:
        return -1
    
def get_all_logging_channels():
    try:
        client = pymongo.MongoClient(config.db_URL)
        db = client["MafiaPlayers"]
        channel = db[config.CHANNEL_COLLECTION]
        channel_list: list[dict] = channel.find({"type":"logging"}).to_list()
        to_return = []
        for c in channel_list:
            to_return.append(c.get("channel_id"))

        return to_return
    
    except:
        return -1

# checks if a given channel is on the list of valid channels for commands.
def is_valid_channel(channel_id) -> bool:
    return True if channel_id in config.valid_channel_ids else False

    
def is_playing(player_username) -> bool:
    for player in config.players:
        if player.username == player_username:
            return True
    return False
    
def add_player(player_name, player_username, player_faction) -> int: 
    for player in config.players:
        if player.name == player_name or player.username == player_username:
            return -1

    new_player = Player(player_name, player_username, player_faction)
    config.players.append(new_player)
    return 0

    
def get_majority() -> int:
    return len(config.players)/2 + 1

# gets all player data from DB
def get_all_players() -> list[Player]:
    try:
        client = pymongo.MongoClient(config.db_URL)
        db = client["MafiaPlayers"]
        players = db[config.COLLECTION]

        all_players = players.find({}).to_list()
        ret_list: list[Player] = []

        for player in all_players:
            # convert dicts to Player objects
            temp = object.__new__(Player)
            temp.__dict__ = player
            ret_list.append(temp)
        
        return ret_list
    except:
        return []
    
def is_majority(player_name: str):
    total_votes = next(player for player in config.players if (player.name == player_name or player.name_lower == player_name)).number_of_votes
    total_players = len(config.players)

    return True if total_votes > (total_players/2) else False
    
def vote(voter_username: str,voted_for_name: str) -> int:

    voter: Player = next(player for player in config.players if player.username == voter_username)

#   can't vote multiple times
    if voter.voted_for != "":
        return -1
    
    # can't vote for players who don't exist
    voted_for_player: Player = next((player for player in config.players if player.name == voted_for_name or player.name_lower == voted_for_name),None)
    if voted_for_player == None:
        return 2
    
    voters_index = config.players.index(voter)
    voted_for_players_index = config.players.index(voted_for_player)
    
    config.players[voted_for_players_index].add_vote(voter.name) # add voter's name to list of votes on that player
    config.players[voters_index].set_voted_for(voted_for_player.name) # set voter's vote as the player they chose
    config.players[voted_for_players_index].set_number_of_votes(config.players[voted_for_players_index].number_of_votes + voter.vote_value) # add vote value to voted player

    return 1000 if is_majority(voted_for_name) else 0
    
def unvote(voter_username) -> int:
    unvoter: Player = next(player for player in config.players if player.username == voter_username)
    
#   havent voted for anybody yet
    if unvoter.voted_for == "":
        return -1

    unvoted_for: Player = next(player for player in config.players if player.name == unvoter.voted_for)
    unvoter_index = config.players.index(unvoter)
    unvoted_for_index = config.players.index(unvoted_for)

    config.players[unvoted_for_index].votes.remove(unvoter.name) # remove unvoter name from list of votes
    config.players[unvoter_index].voted_for = "" # set unvoter's voted_for to empty str
    config.players[unvoted_for_index].number_of_votes -= unvoter.vote_value  # subtract their vote value from the total votes

    return 0

    
def set_vote_value(name: str, value: int) -> int:
    is_real_player = False
    player_index = 0
    for i in range(len(config.players)):
        if config.players[i].name == name or config.players[i].name_lower == name:
            is_real_player = True
            player_index = i
            break

    if not is_real_player:
        return -1

    config.players[player_index].vote_value = value
    return 0
    
def mod_add_vote(player_name: str, value: int) -> int:
    player_to_add_votes: Player = next((player for player in config.players if player.name == player_name or player.name_lower == player_name),None)
    if player_to_add_votes == None:
        return -1
    
    player_index: int = config.players.index(player_to_add_votes)
    config.players[player_index].number_of_votes += value

    return 1000 if is_majority(player_name) else 0
    
def end_day() -> int:
    for player in config.players:
        player.voted_for = ""
        player.votes = []
        player.number_of_votes = 0

    return 0

     
def kill_player(player_name: str) -> int:

    player_to_kill: Player = next(player for player in config.players if player.name.lower() == player_name.lower())

#   remove dead player's vote
    if player_to_kill.voted_for != "":
        unvote(player_to_kill.username)

#   remove other player's votes on dead player
    if len(player_to_kill.votes) > 0:
        for name in player_to_kill.votes:
            their_username = next(player for player in config.players if player.name == name).username
            unvote(their_username)

#   do the deed
    config.players.remove(player_to_kill)
    return 0

def persist_updates():
    try:
        client = pymongo.MongoClient(config.db_URL)
        db = client["MafiaPlayers"]
        players = db[config.COLLECTION]
        channels = db[config.CHANNEL_COLLECTION]

        players.delete_many({})

        
        if len(config.players) > 0:
            # prepare list of dicts to persist
            players_to_persist: list[dict] = []
            for player in config.players:
                players_to_persist.append(player.__dict__)

            # update all player data
            players.insert_many(players_to_persist)

        channels.delete_many({})

        if len(config.valid_channel_ids) + len(config.log_channel_ids) > 0:
            channels_to_persist: list[dict] = []
            for channel in config.valid_channel_ids:
                channels_to_persist.append({"channel_id":channel,"type":"voting"})

            for channel in config.log_channel_ids:
                channels_to_persist.append({"channel_id":channel,"type":"logging"})

            channels.insert_many(channels_to_persist)


    except Exception as e:
        print(e)