import os
from qsBot import QueslarBot
import discord
from discord.ext.commands import CommandNotFound, MissingRole, has_role, MissingRequiredArgument

client = QueslarBot(command_prefix=">", help_command=None)


@client.event
async def on_ready():
  print("Logged in as {}".format(client.user))


my_secret = os.environ['TOKEN']

@client.group(invoke_without_command=True)
async def help(ctx):
  em = discord.Embed(title="Help", description="Use >help <command> for further information.", color=ctx.author.color)
  em.add_field(name="Ping",value=">ping",inline=False)
  em.add_field(name="Get Player Investment Data", value=">player [APIKey]",inline=False)
  em.add_field(name="Bind",value=" >bind",inline=False)
  em.add_field(name="Update",value=">update",inline=False)
  em.add_field(name="Tiles",value=">tiles",inline=False)
  em.add_field(name="Timer",value=">timer [stop|restart|info]",inline=False)
  em.add_field(name="Stored Market Prices", value=">prices",inline=False)

  await ctx.send(embed=em)

@help.command(name="ping")
async def help_ping(ctx):
  em = discord.Embed(title="Ping", description="The bot will send a message if it is active.", color=ctx.author.color)
  em.add_field(name="**Usage**",value=">ping")

  await ctx.send(embed=em)

@help.command(name="player")
async def help_player(ctx):
  em = discord.Embed(title="Get Player Investment Data", description="Displays investment info of the player from the given API key.", color=ctx.author.color)
  em.add_field(name="**Usage**",value=">player [APIKey]")

  await ctx.send(embed=em)

@help.command(name="bind")
async def help_bind(ctx):
  em = discord.Embed(title="Bind", description="Binds the bot to the current channel. The bot will only be able to send messages in the bound channel.", color=ctx.author.color)
  em.add_field(name="**Usage**",value=">bind")

  await ctx.send(embed=em)

@help.command(name="update")
async def help_update(ctx):
  em = discord.Embed(title="Update", description="Pulls information from the game and updates the bot's information.", color=ctx.author.color)
  em.add_field(name="**Usage**",value=">update")

  await ctx.send(embed=em)

@help.command(name="tiles")
async def help_tiles(ctx):
  em = discord.Embed(title="Tiles", description="Displays currently held tiles in the kingdom.", color=ctx.author.color)
  em.add_field(name="**Usage**",value=">tiles")

  await ctx.send(embed=em)

@help.command(name="timer")
async def help_timer(ctx):
  em = discord.Embed(title="Timer", description="Has commands related to the exploration timer.", color=ctx.author.color)
  em.add_field(name="stop",value="Stops the timer.",inline=False)
  em.add_field(name="restart",value="Restarts the timer.",inline=False)
  em.add_field(name="info",value="Displays when the exploration will end.",inline=False)
  em.add_field(name="**Usage**",value=">timer <subcommand>",inline=False)

  await ctx.send(embed=em)

@help.command(name="prices")
async def help_prices(ctx):
  em = discord.Embed(title="Current Market Prices", description="Displays market prices stored by the bot.", color=ctx.author.color)
  em.add_field(name="**Usage**",value=">prices")

  await ctx.send(embed=em)

@client.command()
async def ping(ctx):
  await ctx.send("Pong!")

@client.command()
@has_role("Leader")
async def test(ctx):
  await client.alert_test()


@client.command(name="update")
async def get_info(ctx):
  if await client.update_info():
    await ctx.send("Successfully updated with the latest information.")
  else:
    await ctx.send("Error: Could not update to the latest information.")


@client.command(name="tiles")
async def get_tiles(ctx):
  await ctx.send(embed=client.get_tiles())


@client.command(name="bind")
@has_role("Leader")
async def set_channel(ctx):
  client.set_notification_channel(ctx.channel)
  await ctx.send("Bound notifications to this channel.")


@client.command(name="player")
async def display_investments(ctx, key):
  msg = await client.get_player_investments(key)
  await ctx.send(msg)


@client.command(name="prices")
async def display_prices(ctx):
  msg = await client.get_market()
  await ctx.send(msg)


@client.group(invoke_without_command=True)
async def timer(ctx):
  em = discord.Embed(title="Subcommands", description="", color=ctx.author.color)
  em.add_field(name="stop",value="Stops the timer.",inline=False)
  em.add_field(name="restart",value="Restarts the timer.",inline=False)
  em.add_field(name="info",value="Displays when the exploration will end.",inline=False)
  em.add_field(name="**Usage**",value=">timer <subcommand>",inline=False)

  await ctx.send("Please use a subcommand below.", embed=em)


@timer.command(name="stop")
@has_role("Leader")
async def stop_timer(ctx):
  await client.stop_timer()
  await ctx.send("Stopped the timer.")


@timer.command(name="restart")
@has_role("Leader")
async def restart_timer(ctx):
  await client.restart_timer()
  await ctx.send("Restarted the timer.")
  await print_timer(ctx)


@timer.command(name="info")
async def print_timer(ctx):
  await ctx.send(client.get_exploration_timer())


@client.event
async def on_command_error(ctx, err):
  if isinstance(err, CommandNotFound):
    await ctx.send("Command not available. Use >help for a list of commands.")
    return
  elif isinstance(err, MissingRole):
    await ctx.send("Only leaders can use this command.")
    return
  elif isinstance(err, MissingRequiredArgument):
    await ctx.send("Please add the required argument to the command.")
    return
  raise err


client.run(os.environ['TOKEN'])
