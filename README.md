# QS-Discord-Bot
A Discord bot for the browser game called Queslar.

## Table of Contents
- [About](#about)
- [How to set up](#setup)
- [Bot Commands](#bot-commands)

--------------

### About
This repository contains code to set up a Discord bot for the PBBG called Queslar. It is intended to help notify members of a discord channel of kingdom changes in the game. It is hosted on Repl.it (for now) and uses its custom database to store data. It is built in Python with the discord.py package ([documentation](https://discordpy.readthedocs.io/en/stable/index.html)).


### Setup
First, create a discord bot and set up the hosting solution of your choice. If you are not using Repl.it please edit the code accordingly to store data elsewhere.

To set this bot up, you will need the following:
- A discord bot's token
- A player's API key
- The channel id that the bot will send messages to.
- The role id of that the bot should tag for notifications.

Put them into a file called .env with the following format:  
```
TOKEN=[Token]  
QS_KEY=[API key]  
NOTIFY_CHANNEL=[Channel Id]  
TAG=[roleId]
```
Invite the bot to the server and let the program run.

### Bot Commands
Prefix: ">"

**help**:
Shows the commands that can be given

**ping**:
The bot will send respond if it is active.

**bind**:
Binds the bot to the current channel. The bot will only be able to send messages in the bound channel.

**update**:
Pulls information from the game and updates the bot's information.

**tiles**:
Displays currently held tiles in the kingdom.

**timer <subcommand>**:  
*Subcommand: pause, restart, or info*  
**pause**: Pauses the timer.  
**restart**: Restarts the timer.  
**info**: Displays when the exploration will end.  
