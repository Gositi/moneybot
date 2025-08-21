#!/usr/bin/env python3

#MariaDB
import database
#Discord
import discord
from discord import app_commands
#Dotenv
from dotenv import load_dotenv
import os
#Decimal numbers for currencies
import decimal

load_dotenv ()

#Connect to database
db = database.Database (
    user = os.getenv ("DB_USER"),
    passwd = os.getenv ("DB_PASS"),
    host = "localhost",
    database = "moneybot"
)

#Setup Discord bot
intents = discord.Intents.default ()
client = discord.Client (intents=intents)
tree = app_commands.CommandTree (client)
guild = discord.Object (id = int (os.getenv ("ADMIN_GUILD")))

#Get any users balance
@tree.command (name = "getbal", description = "ADMIN: Get any users balance", guild = guild)
@app_commands.describe (
    user = "User whose balance to see, can also be ID"
)
async def getbal (interaction: discord.Interaction, user: discord.User):
    db.commit ()

    #Make sure user exists in database
    db.ensureUserExists (user.id)
    #Respond with balance
    await interaction.response.send_message (f"User {user.mention} has {db.getBalance (user.id):.2f} money.")

    db.commit ()

#Change the balance of a user
@tree.command (name = "chgbal", description = "ADMIN: Change any users balance", guild = guild)
@app_commands.describe (
    user = "User whose balance to change, can also be ID",
    amount = "Amount of money to change by, up to two decimal places",
    comment = "Optional transaction comment/message"
)
async def chgbal (interaction: discord.Interaction, user: discord.User, amount: float, comment: str = ""):
    db.commit ()

    #Make sure user exists
    db.ensureUserExists (user.id)
    #Round amount to send to two decimal places and verify it is valid
    amount = decimal.Decimal (amount).quantize (decimal.Decimal ("0.01"))
    #Perform transaction
    db.changeBalance (user.id, amount)
    db.logTransaction (None, user.id, amount, comment=comment)
    await interaction.response.send_message (f"Changed balance of {user.mention} by {amount:.2f} with comment:\n{comment}")

    db.commit ()

@client.event
async def on_ready():
    await tree.sync (guild = guild)
    print("Ready!")

client.run (os.getenv("ADMIN_TOKEN"))
