import discord
from discord.ext import commands
import sqlite3
import os
from cogs.SetUp import user_in_db
from cogs.matchmaking import in_queue, in_match, user_in_chall

# connecting to the databases
user_database = sqlite3.connect('users.db')
user_cursor = user_database.cursor()

match_database = sqlite3.connect('matches.db')
match_cursor = match_database.cursor()

challenge_database = sqlite3.connect('challenge.db')
challenge_cursor = challenge_database.cursor()

# check if user has challenge with specific opp
def user_has_chall(user, opp):
    challenge_cursor.execute("SELECT * FROM challenge WHERE p2=?", (user,))
    result = challenge_cursor.fetchone()

    # no result means no challenge
    if result == None:
        return False

    if result[1] == user:
        if result[0] == opp:
            return True
        else:
            return False
    else:
        return False
    
# deletes challenge this user is in
def chall_delete(user):
    challenge_cursor.execute("DELETE FROM challenge WHERE p1=? OR p2=?", (user, user))
    challenge_database.commit()
    return

class tournament(commands.Cog):
    
    def __init__(self, client):
        self.client = client
    
    @commands.command(pass_context = True)    
    async def challenge(self, ctx, member: discord.Member):
        # check if the user has registered in the database, command in SetUp.py
        if user_in_db(ctx.author.name) == False:
            register_command = self.client.get_command('register')
            if register_command:
                await ctx.invoke(register_command)
            else:
                await ctx.send("The 'register' command is unavailable")

        # checking if you or opp are already in a match
        if in_match(ctx.author.name):
            await ctx.send(f"{ctx.author.name} already has a match")
            return
        elif in_match(member.name):
            await ctx.send(f"{member.name} already has a match")
            return
        
        # checking if you or opp are already in queue
        if in_queue(ctx.author.name):
            await ctx.send(f"{ctx.author.name} is aleady in queue")
            return
        elif in_queue(member.name):
            await ctx.send(f"{member.name} is aleady in queue")
            return
        
        # checking if you or opp already sent or received a challenge
        if user_in_chall(ctx.author.name):
            await ctx.send(f"{ctx.author.name} has already sent or received a challenge")
            return
        elif user_in_chall(member.name):
            await ctx.send(f"{member.name} has already sent or received a challenge")
            return

        query = "INSERT INTO challenge VALUES(?,?,?)"
        values = (ctx.author.name, member.name, "N/A")

        challenge_cursor.execute(query, values)
        challenge_database.commit()
        await ctx.send(f"User: {ctx.author.name} has challenged User: {member.name}, respond with !accept @(User) to accept or !cancel to cancel any challenge")
    
    @commands.command(pass_context = True)
    async def accept(self, ctx, member: discord.Member):
        # check if the user has registered in the database, command in SetUp.py
        if user_in_db(ctx.author.name) == False:
            register_command = self.client.get_command('register')
            if register_command:
                await ctx.invoke(register_command)
            else:
                await ctx.send("The 'register' command is unavailable")

        # checking if you or opp are already in a match
        if in_match(ctx.author.name):
            await ctx.send(f"{ctx.author.name} already has a match")
            return
        elif in_match(member.name):
            await ctx.send(f"{member.name} already has a match")
            return
        
        # checking if you or opp are already in queue
        if in_queue(ctx.author.name):
            await ctx.send(f"{ctx.author.name} is aleady in queue")
            return
        elif in_queue(member.name):
            await ctx.send(f"{member.name} is aleady in queue")
            return

        if user_has_chall(ctx.author.name, member.name):
            # add the match into the match database
            query = "INSERT INTO matches VALUES(?, ?, ?, ?)"
            match_cursor.execute(query, (ctx.author.name, member.name, "N/A", "N/A"))
            match_database.commit()

            # delete the challenge 
            chall_delete(ctx.author.name)

            await ctx.send(f"User: {ctx.author.name} has been matched with User: {member.name}")
            await ctx.send(f"Winner should report the match results using !report")
        else:
            await ctx.send("Something went wrong, either you have no challenge or you @ed the wrong user")

    @commands.command(pass_context = True)
    async def cancel(self, ctx):
        # check if the user has registered in the database, command in SetUp.py
        if user_in_db(ctx.author.name) == False:
            register_command = self.client.get_command('register')
            if register_command:
                await ctx.invoke(register_command)
            else:
                await ctx.send("The 'register' command is unavailable")
        
        if user_in_chall(ctx.author.name):

            # delete the challenge 
            chall_delete(ctx.author.name)

            await ctx.send(f"User: {ctx.author.name} has cancelled the current challenge")
        else:
            await ctx.send("Something went wrong, either you have no challenge or you @ed the wrong user")

async def setup(client):
    await client.add_cog(tournament(client))         