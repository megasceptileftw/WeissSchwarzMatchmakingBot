import discord
from discord.ext import commands
import sqlite3
import os
from cogs.SetUp import user_in_db
from table2ascii import table2ascii as t2a, PresetStyle

# connecting to database
user_database = sqlite3.connect('users.db')
user_cursor = user_database.cursor()

match_database = sqlite3.connect('matches.db')
match_cursor = match_database.cursor()

# check rank of specific user
def check_rank(user):
    user_cursor.execute("SELECT * FROM users ORDER BY elo DESC")
    result = user_cursor.fetchall()

    rank = 0
    for entry in result:
        rank = rank + 1
        if user == entry[0]:
            return rank


# personal and leaderboard information
class profile(commands.Cog):
    
    def __init__(self, client):
        self.client = client

    # Top 20 players leaderboard
    @commands.command(pass_context = True)
    async def leaderboard(self, ctx):

        user_cursor.execute("SELECT * FROM users ORDER BY elo DESC")
        result = user_cursor.fetchmany(size=20)

        chart_body = []
        rank = 1
        for user in result:
            chart_body.append([rank, user[0], user[1], user[2], user[3]])
            rank = rank + 1
        
        output = t2a(
            header=["Rank", "User", "Elo", "Ws", "Ls"],
            body=chart_body,
            first_col_heading=True
        )
        
        await ctx.send(f"```\n{output}\n```")

    
    # personal stats
    @commands.command(pass_context = True)
    async def stats(self, ctx):

          # check if the user has registered in the database, function in SetUp.py
        if user_in_db(ctx.author.name) == False:
            await ctx.send(f"User: {ctx.author.name} has not yet registered")
            return
        
        user_cursor.execute("SELECT username, elo, wins, losses FROM users WHERE username=?", (ctx.author.name,))
        result = user_cursor.fetchone()
        
        rank = check_rank(ctx.author.name)

        output = t2a(
            header=["Rank", "User", "Elo", "Ws", "Ls"],
            body=[[rank, result[0], result[1], result[2], result[3]]],
            first_col_heading=True
        )

        await ctx.send(f"```\n{output}\n```")

async def setup(client):
    await client.add_cog(profile(client))  

