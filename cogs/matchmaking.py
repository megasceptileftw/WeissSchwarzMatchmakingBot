import discord
from discord.ext import commands
import sqlite3
import os
import asyncio
import time
from cogs.SetUp import user_in_db

# players who are queueing up are in this list
player_queue = []

# connecting to database
user_database = sqlite3.connect('users.db')
user_cursor = user_database.cursor()

match_database = sqlite3.connect('matches.db')
match_cursor = match_database.cursor()
match_database.execute("CREATE TABLE IF NOT EXISTS matches(p1 STRING, p2 INT, winner INT, loser INT)")

class player:
    def __init__(self, user, elo, wins, losses, in_queue):
        self.user = user
        self.elo = elo
        self.wins = wins
        self.losses = losses
        self.in_queue = in_queue

    async def enter_matchmaking(self):
        player_queue.append(self)
        self.in_queue = True
    
    async def exit_matchmaking(self, opp, ctx):
        if not self.in_queue or not opp.in_queue:
            return
        
        player_queue.remove(self)
        player_queue.remove(opp)

        self.in_queue = False
        opp.in_queue = False

        await ctx.send(f"User: {self.user} has been matched with User: {opp.user}")

    
# fetches data from database and returns with as player class
def fetch_info(user):
    user_cursor.execute("""SELECT username, elo, wins, losses FROM users WHERE username=?""", (user,))
    result = user_cursor.fetchone()
    this_player = player(result[0], result[1], result[2], result[3], False)
    return this_player

class matchmaking(commands.Cog):

    def __init__(self, client):
        self.client = client
    

    @commands.command(pass_context = True)
    async def play(self, ctx):

        if user_in_db(ctx.author.name) == False:
            await ctx.send(f"User: {ctx.author.name} has not yet registered")
            return
        
        p1 = fetch_info(ctx.author.name)
        await p1.enter_matchmaking()
        await ctx.send(f"{p1.user} is in queue")

        while p1.in_queue:
            for opp in player_queue:
                if p1.user != opp.user and abs(p1.elo - opp.elo) <= 300:
                    await p1.exit_matchmaking(opp, ctx)
                    return
            await asyncio.sleep(1)
        
async def setup(client):
    await client.add_cog(matchmaking(client))  
