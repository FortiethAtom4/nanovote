# NANOVOTE



SETUP:

1. Create a channel for voters to discuss in. Type `/setchannel` to allow voting in that channel only.

2. Once all players' roles are sent out, use `/addplayer` to add players to the game.
    - if any players have irregular votes (i.e. doublevoter, negative voter), use `/setvotevalue` to set the value of their votes.

3. Once the game has started, use `/settimer` to start the clock on the day. Voting will be automatically disabled once this timer runs out.

4. Remove players from the vote count using `/kill`. Remember to announce their deaths in the daytime chat.

5. After a majority has been reached, you can reset the vote count using `/resetvotes`. This will re-enable voting commands for players.


List of commands:

Commands available to all players:
- /vote
- /unvote
- /votecount
- /checktime

Mod-only commands:
- /playerinfo

- /addplayer

- /kill

- /settimer

- /setchannel

- /removechannel

- /resetvotes

- /setvotevalue

KNOWN BUGS:
1. setting a player's vote value after they have voted does not update any current votes.
    - e.g. My vote value is 1. I vote for Bennett. My vote value is then set to 2. My vote on Bennett is still 1 and won't change unti I unvote and re-vote.