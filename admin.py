#!/usr/bin/env python3

#Moneybot, a discord bot for handling a virtual currency
#Copyright (C) 2025-2026 Gositi
#License (GPL 3.0) provided in file 'LICENSE'

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

#Set currency symbol
currency = os.getenv ("CURRENCY")

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
    await interaction.response.send_message (f"User {user.mention} has {db.getBalance (user.id):.2f}{currency}.")

    db.commit ()

#Get all users balance
@tree.command (name = "allbal", description = "ADMIN: List all users balances", guild = guild)
async def allbal (interaction: discord.Interaction):
    db.commit ()

    #Get and display balances
    balances = db.getBalances ()
    s = "List of balances:"
    for userID, balance in balances.items ():
        s += f"\n<@{userID}>: {balance:.2f}{currency}"
    await interaction.response.send_message (s)

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
    await interaction.response.send_message (f"Changed balance of {user.mention} by {amount:.2f}{currency} with comment:\n{comment}")

    db.commit ()

#Add an organisation
@tree.command (name = "addorg", description = "ADMIN: Add an organisation account", guild = guild)
@app_commands.describe (
    user = "Owner of the new organisation account",
    name = "Identifier of the organisation account",
    desc = "Optional description of the organisation"
)
async def addorg (interaction: discord.Interaction, user: discord.User, name: str, desc: str = ""):
    db.commit ()

    #Make sure user exists
    db.ensureUserExists (user.id)
    #Check that account doesn't already exist
    if name in db.getAllOrgs().keys():
        await interaction.response.send_message (f"Org `{name}` already exists.")
    else:
        #Create organisation account
        db.createOrgAcc (user.id, name, desc)
        await interaction.response.send_message (f"Org `{name}` created with owner {user.mention} and description:\n{desc}")

    db.commit ()

#Delete an organisation
@tree.command (name = "delorg", description = "ADMIN: Delete an organisation account", guild = guild)
@app_commands.describe (
    name = "Identifier of the organisation account"
)
async def delorg (interaction: discord.Interaction, name: str):
    db.commit ()

    #Transfer remaining funds of account to owner
    user = db.getAllOrgs()[name][0]
    db.transferMoney (
        db.getOrgBalance (name),
        user,
        sender_org = name,
        recipient_id = user,
        comment = "Deletion of org. acc."
    )
    #Delete account
    db.deleteOrgAcc (name)
    await interaction.response.send_message (f"Org `{name}` of user <@{user}> deleted.")

    db.commit ()

#List all organisation accounts
@tree.command (name = "allorgs", description = "ADMIN: List all organisation accounts", guild = guild)
async def allorgs (interaction: discord.Interaction):
    db.commit ()

    #Get and display balances
    orgs = db.getAllOrgs ()
    s = "List of all orgs:"
    for name, (user, balance, desc) in orgs.items ():
        s += f"\n`{name}` (<@{user}>, {desc}): {balance:.2f}{currency}"
    await interaction.response.send_message (s)

    db.commit ()

#List all organisation accounts
@tree.command (name = "getorgs", description = "ADMIN: List all organisation accounts of user", guild = guild)
@app_commands.describe (
    user = "User to list accounts of"
)
async def getorgs (interaction: discord.Interaction, user: discord.User):
    db.commit ()

    #Get and display balances
    orgs = db.getUserOrgs (user.id)
    s = f"List of orgs owned by {user.mention}:"
    for name, (balance, desc) in orgs.items ():
        s += f"\n`{name}` ({desc}): {balance:.2f}{currency}"
    await interaction.response.send_message (s)

    db.commit ()

#Get balance (and owner/description) of an org acc
@tree.command (name = "orgbal", description = "ADMIN: List information about an org acc", guild = guild)
@app_commands.describe (
    name = "Identifier of org acc to view info of"
)
async def orgbal (interaction: discord.Interaction, name: str):
    db.commit ()

    #Get and display balances
    (user, balance, desc) = db.getAllOrgs()[name]
    await interaction.response.send_message (f"Org `{name}` ({desc}) owned by <@{user}> has {balance:.2f}{currency}.")

    db.commit ()

#Get balance (and owner/description) of an org acc
@tree.command (name = "chgorg", description = "ADMIN: Change the balance of an org account", guild = guild)
@app_commands.describe (
    name = "Identifier of org account",
    amount = "Amount to change balance by",
    comment = "Optional comment of change"
)
async def chgorg (interaction: discord.Interaction, name: str, amount: float, comment: str = ""):
    db.commit ()

    #Check that org acc exists
    if not name in db.getAllOrgs().keys():
        await interaction.response.send_message (f"Org `{name}` does not exist.")
    else:
        #Round amount to send to two decimal places and verify it is valid
        amount = decimal.Decimal (amount).quantize (decimal.Decimal ("0.01"))
        #Perform transaction
        db.changeOrgBalance (name, amount)
        db.logTransaction (amount, None, recipient_org=name, comment=comment)
        await interaction.response.send_message (f"Changed balance of `{name}` by {amount:.2f}{currency} with comment:\n{comment}")

    db.commit ()

#Change owner of org
@tree.command (name = "movorg", description = "ADMIN: Change owner of org acc", guild = guild)
@app_commands.describe (
    name = "Identifier of org account",
    user = "New owner"
)
async def movorg (interaction: discord.Interaction, name: str, user: discord.User):
    db.commit ()

    #Change owner
    db.changeOrgOwner (name, user.id)
    await interaction.response.send_message (f"Changed owner of `{name}` to {user.mention}.")

    db.commit ()

#Get the net worth of a user
@tree.command (name = "networth", description = "ADMIN: Calculate the net worth of a user", guild = guild)
@app_commands.describe (
    user = "User to calculate net worth of"
)
async def networth (interaction: discord.Interaction, user: discord.User):
    db.commit ()

    #Get and display balances
    orgs = db.getUserOrgs (user.id)
    networth = sum([balance for _, (balance, _) in orgs.items()])
    await interaction.response.send_message (f"User {user.mention} has a net worth of {networth:.2f}{currency}.")

    db.commit ()

@client.event
async def on_ready():
    await tree.sync (guild = guild)
    print("Ready!")

client.run (os.getenv("ADMIN_TOKEN"))
