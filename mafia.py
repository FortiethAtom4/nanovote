# representation of a mafia game.


class Player:
    def __init__(self,name: str, username: str, faction: str = "Town"):
        self.name = name
        self.faction = faction
        self.username = username
        self.votes: list[str] = []
        self.voted_for = ""

#   default faction is "Town," so this method sets to other factions.
    def set_faction(self,faction: str):
        self.faction = faction

    def set_votes(self,value):
        self.votes = value

    def to_string(self):
        voters = ""
        for voter in self.votes:
            voters += voter + ", "
        return f"[{self.name} ({len(self.votes)}): {voters}]"
    
    def add_vote(self,voter):
        self.votes.append(voter)

    def remove_vote(self,voter):
        self.votes.remove(voter)

    def set_voted_for(self,name):
        self.voted_for = name
