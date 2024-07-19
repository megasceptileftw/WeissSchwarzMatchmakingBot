#import required dependencies
import discord
from discord.ext import commands
import sqlite3
import asyncio
import os

# import various tokens
from apikeys import *

intents = discord.Intents.all()
intents.members = True

client = commands.Bot(command_prefix = '!', intents = intents)

@client.event
async def on_ready():
    await client.change_presence(activity=discord.Streaming(name='Huniepop', url='https://www.twitch.tv/alexxvgc'))
    print("The bot is now ready for use!")
    print("-----------------------------")

# initializing database
database = sqlite3.connect('users.db')
cursor = database.cursor()
database.execute("CREATE TABLE IF NOT EXISTS users(username STRING, elo INT, wins INT, losses INT)")

# solved error using this page https://stackoverflow.com/questions/45892045/nameerror-name-asyncio-is-not-defined-in-running-discord-bot
async def load_extensions():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await client.load_extension(f"cogs.{filename[:-3]}")

async def main():
    async with client:
        await load_extensions()
        await client.start(BOTTOKEN)


asyncio.run(main())