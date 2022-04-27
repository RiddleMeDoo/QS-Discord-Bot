# QS Discord Bot

A Discord bot for the browser game called Queslar.

## Table of Contents

-   [About](#about)
-   [How to set up](#setup)
-   [Bot Commands](#bot-commands)
-   [Explanation of the files](#code)

---

### About

This repository contains code to set up a Discord bot for the PBBG called Queslar. It is intended to help notify members of a discord channel of kingdom changes in the game. It can be hosted on your computer as long as you have the correct packages installed. This bot is also set up to run on [Heroku](https://heroku.com) (an online hosting service) and uses [Redis](https://redis.io/) as its database. It is built in Python with the discord.py package ([documentation](https://discordpy.readthedocs.io/en/stable/index.html)) with an object-oriented approach.

### Setup

First, create a discord bot and set up the hosting solution of your choice. If you are hosting it on Heroku, then you will find that the Procfile, requirements.txt, and runtime.txt is set up for you already. Please find and follow a tutorial if you want to know how to run it on Heroku. You will also need to set up your database, whether it is Redis or some other solution. If you are using another database, then all you need to do is to edit the database.py file.

To set this bot up, you will need the following:

-   A discord bot's token
-   A player's Queslar API key
-   The channel id that the bot will send messages to.
-   Your database credentials. For Redis it is URL, port, and password.

If you are not using an online hosting service, copy and paste the following into a file called .env with the same format: (see code chunk below)
If you are using a hosting service, put them into the appropriate "secret", "env", or "config" vars with the following:

```
TOKEN=[Token]
QS_KEY=[API key]
NOTIFY_CHANNEL=[Channel Id]
REDIS_HOSTNAME=[Redis host name]
REDIS_PORT=[Redis port number]
REDIS_PASSWORD=[Redis password to the database, may be optional]
```

**Bonus: Setting it up on the computer**  
If you're hosting it yourself on the computer, please install Python 3.8+ and pip via the command line. I personally use Linux for this (WSL). Once you have pip installed, then enter `pip install [package_name]`. The `package_name`s can be found in `requirements.txt`. Install one on each line.

Invite the bot to the server and let the program run on Python.  
`NOTE: Make sure the bot can mention @here and the leader role.`

### Bot Commands

Prefix: ">"

**help**:
Shows the commands that can be given

**ping**:
The bot will send a response if it is active.

**bind** (privileged command):
Binds the bot to the current channel. The bot will only be able to send messages in the bound channel. Only users with the role "Leader" may use it.

**update**:
Pulls information from the game and updates the bot's information.

**player [APIKey]**:
Given an API key, it displays a player's investments, income, and equipment stats.

**tiles**:
Displays currently held tiles in the kingdom.

**timer \<subcommand>** (privileged command):  
_Subcommand: stop, restart, or info_  
Only users with the role "Leader" may use it.  
**stop**: Stops the timer.  
**restart**: Restarts the timer.  
**info**: Displays when the exploration will end.

### Code

Here is an explanation of each Python file in this repository and what they do:

**main.py**  
The main entry into the program, this is what you run to run the entire thing. It creates an instance of the bot, and handles any commands that users use on the bot. 

**qsBot.py**  
The bot will handle commands using functions written in this file. The functions are separated from the commands for simple organization. There is also a function that runs every 5 minutes to check on tile updates, in hindsight this should have been in a separate file. I'm lucky that the scheduled task can still access the instance of the bot when it runs every 5 minutes.

**calculator.py**  
This is where misc functions dedicated to calculating the investment amounts go.

**database.py**
This is where database operations happen. The detached nature of this file means that the database can be easily replaced to some other database.

**market.py and tile.py**
These are objects, or "models". The bot will contain an instance of the market and tile, and will use them to do market/tile-specific operations. Yeah I just wanted to be object oriented.
