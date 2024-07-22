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


# fetches data from database and returns with as player class
def fetch_info(user):
    user_cursor.execute("""SELECT username, elo, wins, losses FROM users WHERE username=?""", (user,))
    result = user_cursor.fetchone()
    this_player = player(result[0], result[1], result[2], result[3], False)
    return this_player

# checks if username is in matches and the result is still N/A
def in_match(user):
    match_cursor.execute("SELECT * FROM matches")
    result = match_cursor.fetchall()

    for row in result:
        if user in row:
            if row[2] == "N/A":
                return True
    
    return False

# checks if username is in queue, true if it is, false if it isn't
def in_queue(user):

    for x in player_queue:
        if user == x.user:
            return True

    return False


# player class with player info and matchmaking functions
class player:
    def __init__(self, user, elo, wins, losses, is_in_queue):
        self.user = user
        self.elo = elo
        self.wins = wins
        self.losses = losses
        self.is_in_queue = is_in_queue

    # puts player into player_queue and sets is_in_queue to True
    async def enter_matchmaking(self):
        player_queue.append(self)
        self.is_in_queue = True
    
    # matches player with opponent, removes player and opponent from queue, adds match to matches database
    async def exit_matchmaking(self, opp, ctx):
        if not self.is_in_queue or not opp.is_in_queue:
            return
        
        player_queue.remove(self)
        player_queue.remove(opp)

        self.is_in_queue = False
        opp.is_in_queue = False

        # add match into database with winner and loser set to "N/A"
        query = "INSERT INTO matches VALUES(?, ?, ?, ?)"
        match_cursor.execute(query, (self.user, opp.user, "N/A", "N/A"))
        match_database.commit()

        await ctx.send(f"User: {self.user} has been matched with User: {opp.user}")
        await ctx.send(f"Winner should report the match results using !report")


class matchmaking(commands.Cog):

    def __init__(self, client):
        self.client = client
    

    # queues players up for a match 
    @commands.command(pass_context = True)
    async def play(self, ctx):

        # check if the user has registered in the database, function in SetUp.py
        if user_in_db(ctx.author.name) == False:
            await ctx.send(f"User: {ctx.author.name} has not yet registered")
            return

        # checking if already in a match
        if in_match(ctx.author.name):
            await ctx.send(f"{ctx.author.name} already has a match")
            return
        
        # checking if already in queue
        if in_queue(ctx.author.name):
            await ctx.send(f"{ctx.author.name} is aleady in queue")
            return

        # fetch user data, put info into player class
        p1 = fetch_info(ctx.author.name)
        
        # enter matchmaking queue
        await p1.enter_matchmaking()
        await ctx.send(f"{p1.user} is in queue, if you don't find an opponent after 15 minutes you will leave the queue")

        start = time.time()

        # checking for suitable opponent
        while p1.is_in_queue:
            for opp in player_queue:
                if p1.user != opp.user and abs(p1.elo - opp.elo) <= 300:
                    await p1.exit_matchmaking(opp, ctx)
                    return
            await asyncio.sleep(1)

            # checking if time since start is greater than 15 minutes or 900 seconds, if so exiting queue
            if ((time.time() - start) > 900):
                await ctx.send("Exiting queue")
                player_queue.remove(p1)
                return
            
        return
    

    # leaves the queue 
    @commands.command(pass_context = True)
    async def leave(self, ctx):
        # checking if player is actually in the queue
        if not in_queue(ctx.author.name):
            await ctx.send(f"User: {ctx.author.name} is not in queue currently")
            return
        
        # checking if already in a match
        if in_match(ctx.author.name):
            await ctx.send(f"User: {ctx.author.name} is in a match")
            return
        
        for x in player_queue:
            if ctx.author.name == x.user:
                player_queue.remove(x)
                await ctx.send(f"User: {ctx.author.name} has been removed from the queue")
                return

async def setup(client):
    await client.add_cog(matchmaking(client))  
