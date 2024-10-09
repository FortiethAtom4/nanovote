# representation of a mafia game.

common_currency_id = "2f85db1c-ef92-4bbc-89dc-ccdcdef0ad94"

class Player:
    def __init__(self,name: str, username: str, faction: str = "Town"):
        self.name = name
        self.faction = faction
        self.username = username
        self.number_of_votes = 0 # this value is not necessarily equal to length of self.votes
        self.votes: list[str] = []
        self.voted_for = ""
        self.vote_value = 1 # used for doublevoters, negative voters, etc.

#   default faction is "Town," so this method sets to other factions.
    def set_faction(self,faction: str):
        self.faction = faction

    def set_votes(self,value):
        self.votes = value

    def set_number_of_votes(self,value):
        self.number_of_votes = value

    def to_string(self,admin: bool):
        voters = ""
        vl = len(self.votes)
        if vl > 0:
            for i in range(vl - 1):
                voters += self.votes[i] + ", "
            voters += self.votes[vl - 1]
        return_string = f"[{self.name} ({self.number_of_votes}): {voters}]"
        if not admin:
            return return_string
        # add info if admin
        return_string += f"\nFaction: {self.faction}"
        return_string += f"\nVote value: {self.vote_value}"
        return_string += f"\nCurrently voting for: {self.voted_for}"
        return return_string

    def set_vote_value(self,value):
        self.vote_value = value
    
    def add_vote(self,voter):
        self.votes.append(voter)

    def remove_vote(self,voter):
        self.votes.remove(voter)

    def set_voted_for(self,name):
        self.voted_for = name

class Item:
    @staticmethod
    def load_item_from_db_entry(item):
        return Item(item.get("item_name"), item.get("price"), item.get("type"))

    def __init__(self,item_name: str, price: int, type:int):
        self.item_name = item_name
        self.price = price
        # type 0 is non targeted
        # type 1 is targeted
        self.type = type

    def get_item_name(self):
        return self.item_name

    def get_price(self):
        return self.price

    def get_type(self):
        return self.type
    
    def get_shop_display(self):
        return "[" + self.get_item_name() + ": " + str(self.get_price()) + "]"
    
    def get_db_form(self):
        return { "item_name": self.get_item_name(), "price": self.get_price(), "type": self.get_type() }
    
class Wallet:
    @staticmethod
    def load_wallet_from_db_entry(entry):
        return Wallet(entry.get("username"), entry.get("amount"))

    def __init__(self,username: str,amount:int):
        self.username = username
        self.amount = amount

    def is_common(self):
        return self.username == common_currency_id
    
    def get_username(self):
        return self.username
    
    def get_amount(self):
        return self.amount
    
    def can_add_currency(self, amount):
        return self.get_amount() + amount >= 0
    
    def get_db_form(self):
        return { "username": self.get_username(), "amount": self.get_amount() }
    
    def get_list_display(self):
        if self.is_common():
            return "[Common wallet: " + str(self.amount) + "]"
        return "[" + self.get_username() + ": " + str(self.amount) + "]"