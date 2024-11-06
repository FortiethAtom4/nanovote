# NANOVOTE



SETUP:

1. Create a channel for voters to discuss in. Type `/setchannel` to allow voting in that channel only.

2. Once all players' roles are sent out, use `/addplayer` to add players to the game.
    - if any players have irregular votes (i.e. doublevoter, negative voter), use `/setvotevalue` to set the value of their votes.

3. Once the game has started, use `/settimer` to start the clock on the day. Voting will be automatically disabled once this timer runs out.

4. Remove players from the vote count using `/kill`. Remember to announce their deaths in the daytime chat.

5. After a majority has been reached, you can reset the vote count using `/resetvotes`. This will re-enable voting commands for players.


List of commands:

## PLAYER COMMANDS
All users have access to these commands.

- `/checktime`: Gets the amount of time left before the day ends.
- `/votecount`: Gets a list of all players in the game, their vote counts, the time remaining in the day, and the number of votes needed for majority.
- `/vote [playername]`: Places your vote for a player to be lynched. Available for living players only.
- `/unvote`: Revokes your vote on a player. Available for living players only.
- `/help player`: Displays this message.'

## MOD COMMANDS
Only users with the Moderator or Main Moderator roles can use these commands.
### SETUP
- `/addplayer [player_name] [player_username] [faction]`: Adds a player to the game. 
- `/help mod`: Displays this message.
- `/playerinfo`: Displays all information about living players in the game. This includes votecount info as well as their faction and vote value.
- `/removechannel`: Removes a voting flag from a channel.
- `/removelogchannel`: Removes a logging flag from a channel.
- `/setchannel`: Flags a channel for voting. Players may only vote in channels set with this command.
- `/setlogchannel`: Flags a channel for logging. The bot will record votes and unvotes in log channels.
- `/setmod`: Saves your username. You will be sent a DM when voting ends. NOTE: Only one username can be saved at a time. 
### TIMER
- `/settimer [time_hours] (time_minutes)`: Sets the timer for the day to end. Players can vote once the timer is started. The mod who sets this timer will be sent a DM when time is up.
- `/addtime [time_hours] (time_minutes)`: Adds time to the timer. Negative values subtract from the timer.
- `/toggletimer`: Toggles the timer on and off. Players cannot vote while the timer is off.
### VOTE MANAGEMENT
- `/resetvotes`: Resets all players' votes and sets their vote counts to 0.
- `/setvotevalue [player_name] [value]`: Sets the value of a player's vote. Default value is 1.
- `/addvotes [player_name] [value]`: Manually add votes to a player. Negative values subtract votes. WARNING: Adding votes this way CAN trigger majority.
### END OF DAY
- `/togglemajority`: Toggles the majority flag on or off. Players cannot vote if the majority flag is toggled. 
- `/kill [player_name]`: Kills a player, removing them from the game.

KNOWN BUGS:
1. setting a player's vote value after they have voted does not update any current votes.
    - e.g. My vote value is 1. I vote for Bennett. My vote value is then set to 2. My vote on Bennett is still 1 and won't change unti I unvote and re-vote.


# HOW TO ADD YOUR OWN CUSTOM COMMANDS

The bot has been organized so that adding new commands is easy to do without getting too deep in the weeds of it all. Here are the high-level steps involved in making a new class of commands and adding them to the bot:
1. Create a copy of one of the `.py` files in the `cogs` folder. Make sure your copy is also in that same folder.
2. Change the filename to whatever you want. 
3. In your new file, change the class name at the top to a name of your choosing. Just make sure there isn't another cog with the same name. 
    - After you rename the class, you'll need to change the name within the `setup` method at the bottom of the file to the name you chose.
4. Delete all the code in that cog class EXCEPT the function called `__init__`. Be careful not to delete `setup`.
5. Code whatever you want in your new mostly-empty class. If you're unfamiliar with making Discord bot commands, feel free to copy-paste commands from the other cogs to try them out, or peruse the Pycord documentation for more info.
6. In `config.py`, add the name of your file to the `cogs` list variable. Make sure not to include the `.py` extension; you just need the base name. 
If everything else has been done right, your commands should now be available in the bot for testing/usage when you run `python nanovote.py`.