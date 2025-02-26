import discord
from discord.ext import commands
from discord import Member
from discord.ext.commands import has_permissions, MissingPermissions
import requests
import sqlite3
import os

# connecting to database
database = sqlite3.connect('users.db')
cursor = database.cursor()

# check if a username is in database
# if it is in the database return True, if it is not return False
def user_in_db(username):
    cursor.execute("""SELECT username FROM users WHERE username=?""", (username,))
    result = cursor.fetchone()
    if result:
        return True
    else:
        return False

class SetUp(commands.Cog):

    def __init__(self, client):
        self.client = client


    # register users into matchmaking, add them into the database, adds desired matchmaking role
    @commands.command(pass_context = True)
    async def register(self, ctx):
        
        # checks if user is already registered and returns if they have already registered
        if user_in_db(ctx.author.name):
            await ctx.send(f"User: {ctx.author.name} has already registered")
            return
        
        query = "INSERT INTO users VALUES(?, ?, ?, ?)" 
        # fetching desired role for matchmaking
        role_name = "Matchmaking"
        role = discord.utils.get(ctx.author.guild.roles, name=role_name)
    
        try:
            # registering user to database with starting elo of 1000
            cursor.execute(query, (ctx.author.name, 1000, 0, 0))
            database.commit()
            await ctx.send(f"User: {ctx.author.name} has been added to matchmaking")

            # adding desired role to matchmaking user
            await ctx.author.add_roles(role)
            await ctx.send(f"User: {ctx.author.name} has been given the {role_name} role")

        except Exception as e:
            await ctx.send(f"An error has occurred: {e}")
    

    # unregister users, remove them from thedatabase, removes role previously added
    @commands.command(pass_context = True)
    async def unregister(self, ctx):    
        
        # fetching desired role for removal
        role_name = "Matchmaking"
        role = discord.utils.get(ctx.author.guild.roles, name=role_name)

        if user_in_db(ctx.author.name):
            # deleting user from database
            cursor.execute("DELETE FROM users WHERE username=?", (ctx.author.name,))
            database.commit()
            await ctx.send(f"User: {ctx.author.name} has been removed from matchmaking")
            
            # removing desired role
            await ctx.author.remove_roles(role)
            await ctx.send(f"User: {ctx.author.name} no longer has the {role_name} role")
        else:
            await ctx.send(f"User: {ctx.author.name} not registered yet")

    @commands.command(aliases=["quit"])
    @commands.has_permissions(administrator=True)
    async def close(client, ctx):
        try:
            await ctx.send("The bot is ending :(")
            exit()
        except Exception as e:
            await ctx.send(f"An error has occurred: {e}")

async def setup(client):
    await client.add_cog(SetUp(client))    