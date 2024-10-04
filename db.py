import pymongo
import os
from dotenv import load_dotenv
import pymongo.collection
from math import trunc

# local imports
from mafia import Player

load_dotenv()
USER = os.getenv("MONGODB_USER")
PASS = os.getenv("MONGODB_PASS")
CHANNEL_COLLECTION = os.getenv("DB_CHANNEL_COLLECTION")
# different db collections, one for dev env one for mafiacord
COLLECTION = os.getenv("DB_COLLECTION")
db_URL = f"mongodb+srv://{USER}:{PASS}@nanobot.lab1zmc.mongodb.net/"

# tests connection to database.
def test_connection():
    try:
        client = pymongo.MongoClient(db_URL)
        return client
    except:
        return -1
    
# persists valid voting channel for game.
def persist_voting_channel(channel_id):
    try:
        client = pymongo.MongoClient(db_URL)
        db = client["MafiaPlayers"]
        channel = db[CHANNEL_COLLECTION]
        if len(dict(channel.find({"channel_id":channel_id}))) > 0:
            return -1
        
        # type separates voting channels from logging channels
        to_insert = {"channel_id":channel_id,"type":"voting"}
        channel.insert_one(to_insert)
        return 0
    except:
        print("failed")
        return 1

# fetches all valid channels
def get_all_valid_channels():
    try:
        client = pymongo.MongoClient(db_URL)
        db = client["MafiaPlayers"]
        channel = db[CHANNEL_COLLECTION]
        channel_list: list[dict] = channel.find({"type":"voting"}).to_list()
        to_return = []
        for c in channel_list:
            to_return.append(c.get("channel_id"))

        return to_return
    
    except:
        return -1
    
def persist_logging_channel(channel_id):
    try:
        client = pymongo.MongoClient(db_URL)
        db = client["MafiaPlayers"]
        channel = db[CHANNEL_COLLECTION]
        if len(dict(channel.find({"channel_id":channel_id}))) > 0:
            return -1
        
        # type separates voting channels from logging channels
        to_insert = {"channel_id":channel_id,"type":"logging"}
        channel.insert_one(to_insert)
        return 0
    except:
        return 1
    
def get_all_logging_channels():
    try:
        client = pymongo.MongoClient(db_URL)
        db = client["MafiaPlayers"]
        channel = db[CHANNEL_COLLECTION]
        channel_list: list[dict] = channel.find({"type":"logging"}).to_list()
        to_return = []
        for c in channel_list:
            to_return.append(c.get("channel_id"))

        return to_return
    
    except:
        return -1

# checks if a given channel is on the list of valid channels for commands.
def is_valid_channel(channel_id) -> bool:
    try:
        client = pymongo.MongoClient(db_URL)
        db = client["MafiaPlayers"]
        channel = db[CHANNEL_COLLECTION]

        ret: list[dict] = channel.find({})
        for c in ret:
            if c.get("channel_id") == channel_id:
                return True
        return False

    except:
        return 1

# remove a channel from list of valid channels.
def remove_channel(channel_id: int) -> int:
    try:
        client = pymongo.MongoClient(db_URL)
        db = client["MafiaPlayers"]
        channel = db[CHANNEL_COLLECTION]

        channel.delete_one({"channel_id":channel_id})
        return 0

    except Exception as e:
        print("channel remove failed:\n",e)
        return 1

    
def is_playing(player_username) -> bool:
    try:
        client = pymongo.MongoClient(db_URL)
        db = client["MafiaPlayers"]
        players = db[COLLECTION]

        return players.find_one({'username':player_username})

    except:
        return False
    
def add_player(player_name, player_username, player_faction) -> int: 
    try:
        client = pymongo.MongoClient(db_URL)
        db = client["MafiaPlayers"]
        players = db[COLLECTION]

        isnewplayer = list(players.find({"username":player_username}))
        is_unique_name = list(players.find({"name":player_name}))
        if len(isnewplayer) != 0 or len(is_unique_name) != 0:
            return -1
        
        new_player = Player(player_name, player_username, player_faction)
        players.insert_one(vars(new_player))
        return 0

    except:
        return 1
    
def get_majority() -> int:
    try:
        client = pymongo.MongoClient(db_URL)
        db = client["MafiaPlayers"]
        players = db[COLLECTION]

        return trunc(len(players.find({}).to_list())/2 + 1)
    except Exception as e:
        print(e)
        return -1
    
def get_all_players() -> list[Player]:
    try:
        client = pymongo.MongoClient(db_URL)
        db = client["MafiaPlayers"]
        players = db[COLLECTION]

        all_players = players.find({})

        player_list = []
        for player in all_players:
            player = dict(player)
            temp = Player(player.get("name"),player.get("username"))
            temp.set_faction(player.get("faction"))
            temp.set_votes(player.get("votes"))
            temp.set_vote_value(player.get("vote_value"))
            temp.set_voted_for(player.get("voted_for"))
            temp.set_number_of_votes(player.get("number_of_votes"))
            player_list.append(temp)
        
        return player_list
    except:
        return []
    
def is_majority(players: list[dict], player_name: str):
    # total_votes = dict(players.find_one({'name':player_name})).get("number_of_votes")
    total_votes = next(player for player in players if player["name"] == player_name).get("number_of_votes")
    total_players = len(players)

    return True if total_votes > (total_players/2) else False
    
def vote(voter_username: str,voted_for_name: str) -> int:
    try:
        client = pymongo.MongoClient(db_URL)
        db = client["MafiaPlayers"]
        players = db[COLLECTION]

        all_players: list[dict] = players.find({}).to_list()
        voter = next(player for player in all_players if player["username"] == voter_username)

        voter_name = voter.get("name")
        voter_vote_value = voter.get("vote_value")


#       can't vote multiple times
        already_voted = voter.get("voted_for")
        if already_voted != "":
            return -1
        
        # can't vote for players who don't exist
        # next((item for item in dicts if item["name"] == "Pam"), None)
        voted_for_player = next((player for player in all_players if player["name"].casefold() == voted_for_name.casefold()),None)
        if voted_for_player == None:
            return 2
        
        voted_for_name = voted_for_player.get("name") # because the input value might be lowercase and db version is not

        players.update_one({'name':str(voted_for_name)},{'$push':{'votes':str(voter_name)}})
        players.update_one({'name':str(voter_name)},{'$set':{'voted_for':str(voted_for_name),}})
        players.update_one({'name':str(voted_for_name)},{'$inc':{'number_of_votes':int(voter_vote_value)}})
        
        # this is necessary to update all_players with the new number of votes
        next(player for player in all_players if player["name"] == voted_for_name)["number_of_votes"] += voter_vote_value


        return 1000 if is_majority(all_players,voted_for_name) else 0

    except Exception as e:
        print(e)
        return 1
    
def unvote(voter_username) -> int:
    try:
        client = pymongo.MongoClient(db_URL)
        db = client["MafiaPlayers"]
        players = db[COLLECTION]

        unvoter = dict(players.find_one({"username":voter_username}))
        unvoter_vote_value = unvoter.get("vote_value")
        
#       havent voted for anybody yet
        to_unvote_name = unvoter.get("voted_for")
        if to_unvote_name == "":
            return -1

        unvoter_name = unvoter.get("name")

        players.update_one({"name":to_unvote_name},{'$pull':{'votes':unvoter_name}})
        players.update_one({'name':unvoter_name},{'$set':{'voted_for':""}})
        players.update_one({'name':to_unvote_name},{'$inc':{'number_of_votes':int(-unvoter_vote_value)}})

        return 0

    except:
        return 1
    
def set_vote_value(name: str, value: int) -> int:
    try:
        client = pymongo.MongoClient(db_URL)
        db = client["MafiaPlayers"]
        players = db[COLLECTION]

        is_real_player = players.find_one({"name":name})
        if is_real_player == None:
            return -1

        players.update_one({"name":name},{"$set":{"vote_value":value}})
        return 0

    except Exception as e:
        return 1
    
def mod_add_vote(player_name: str, value: int) -> int:
    try:
        client = pymongo.MongoClient(db_URL)
        db = client["MafiaPlayers"]
        players = db[COLLECTION]

        players.find_one_and_update({"name":player_name},{'$inc':{'number_of_votes':value}})
        if players == None:
            return -1
        
        all_players = players.find({}).to_list()
        return 1000 if is_majority(all_players,player_name) else 0

    except Exception as e:
        print(e)
        return 1
    
def end_day() -> int:
    try:
        client = pymongo.MongoClient(db_URL)
        db = client["MafiaPlayers"]
        players = db[COLLECTION]

        players.update_many({},{'$set':{'voted_for':""}})
        players.update_many({},{'$set':{'votes':[]}})
        players.update_many({},{'$set':{'number_of_votes':0}})

        return 0

    except:
        return 1
    
#   Known issue: killing player does not reset their votes or others' votes. 
def kill_player(player_name) -> int:
    try:
        client = pymongo.MongoClient(db_URL)
        db = client["MafiaPlayers"]
        players = db[COLLECTION]

        player = dict(players.find_one({"name":player_name}))

#       remove dead player's vote
        player_username = player.get("username")
        unvote(player_username)

#       remove other player's votes on dead player
        votes_on_player = player.get("votes")
        for player in votes_on_player:
            their_username = dict(players.find_one({"name":player})).get("username")
            unvote(their_username)

#       do the deed
        players.delete_one({'name':player_name})
        return 0

    except Exception as e:
        print(e)
        return 1
    
def get_name_from_username(username: str):
    try:
        client = pymongo.MongoClient(db_URL)
        db = client["MafiaPlayers"]
        players = db[COLLECTION]

        return dict(players.find_one({"username":username})).get("name")

    except Exception as e:
        print(e)
        return ""