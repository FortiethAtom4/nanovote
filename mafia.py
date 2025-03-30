# representation of a mafia game.


class Player:
    def __init__(self,name: str, username: str, faction: str = "Town"):
        self.name = name
        self.faction = faction
        self.username = username
        self.number_of_votes = 0 # this value is not necessarily equal to length of self.votes
        self.votes: list[str] = []
        self.voted_for = ""
        self.vote_value = 1 # used for doublevoters, negative voters, etc.
        self.mafia: bool = False # for mafia list


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
        return_string += f"\nFaction: {self.faction} {"\(Mafia\)" if self.mafia else ""}"
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

class CustomAbility:
     
     def __init__(self):
         pass