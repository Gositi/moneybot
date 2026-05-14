#!/usr/bin/env python3

#Moneybot, a discord bot for handling a virtual currency
#Copyright (C) 2025-2026 Gositi, Retha
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
#Enum types for multi-choice interactions
import enum

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
guild = discord.Object (id = int (os.getenv ("GUILD")))

#Set currency symbol
currency = os.getenv ("CURRENCY")

#Get your own balance
@tree.command (name = "bal", description = "Get your balance", guild = guild)
@app_commands.describe (
    org = "Optional organisation account to view balance of"
)
async def bal (interaction: discord.Interaction, org: str = ""):
    db.commit ()
    org = db.truncate (org)

    #Make sure user exists
    db.ensureUserExists (interaction.user.id)

    if org:
        if not org in db.getUserOrgs(interaction.user.id).keys():
            await interaction.response.send_message (f"You are not the owner of `{org}`!", ephemeral=True)
        else:
            balance = db.getOrgBalance (org)
            await interaction.response.send_message (f"The account `{org}` has {balance:.2f}{currency}.", ephemeral=True)
    else:
        balance = db.getBalance (interaction.user.id)
        await interaction.response.send_message (f"You have {balance:.2f}{currency} in your personal account.", ephemeral=True)

    db.commit ()

#Pay/transfer money to someone else
@tree.command (name = "payusr", description = "Transfer money to a user", guild = guild)
@app_commands.describe (
    recipient = "Recipient user of transfer",
    amount = "Amount of money to transfer, up to two decimal places",
    org = "Optional organisation account to send from",
    comment = "Optional transaction comment/message"
)
async def payusr (interaction: discord.Interaction, recipient: discord.User, amount: float, org: str = "", comment: str = ""):
    await pay (interaction, org, recipient, None, amount, comment)

#Pay/transfer money to an organisation
@tree.command (name = "payorg", description = "Transfer money to an organisation", guild = guild)
@app_commands.describe (
    recipient = "Recipient organisation of transfer",
    amount = "Amount of money to transfer, up to two decimal places",
    org = "Optional organisation account to send from",
    comment = "Optional transaction comment/message"
)
async def payorg (interaction: discord.Interaction, recipient: str, amount: float, org: str = "", comment: str = ""):
    await pay (interaction, org, None, recipient, amount, comment)

#General-purpose function to perform a transaction with
async def pay (interaction, org, recipient_user, recipient_org, amount, comment):
    db.commit ()

    if org: org = db.truncate (org)
    if recipient_org: recipient_org = db.truncate (recipient_org)

    #Make sure sender exists
    db.ensureUserExists (interaction.user.id)

    #Round amount to send to two decimal places and verify it is valid
    amount = decimal.Decimal (amount).quantize (decimal.Decimal ("0.01"))
    if amount < 0:
        await interaction.response.send_message (f"You cannot send a negative amount of money", ephemeral=True)
        return
    if not (recipient_user or recipient_org):
        raise Exception("Either recipient_user or recipient_org needs to be specified.")

    #Make sure recipient exists
    if recipient_user:
        db.ensureUserExists (recipient_user.id)
    if recipient_org and not recipient_org in db.getAllOrgs().keys():
        await interaction.response.send_message (f"Organisation `{recipient_org}` does not exist.", ephemeral=True)
        return
        
    #Check that the sender owns the potential sender org
    if org and not org in db.getUserOrgs(interaction.user.id).keys():
        await interaction.response.send_message (f"You are not the owner of `{org}`!", ephemeral=True)
        return
        
    #Check that the sender has enough money
    if org:
        funds = db.getOrgBalance (org)
    else:
        funds = db.getBalance (interaction.user.id)
    if amount > funds:
        await interaction.response.send_message (f"Insufficient balance, the selected account currently has {funds:.2f}{currency} left.", ephemeral=True)
        return
        
    #Set recipient id variable
    if recipient_user:
        recipient_id = recipient_user.id
    else:
        recipient_id = None

    #Transfer money
    db.transferMoney (amount, interaction.user.id, org, recipient_id, recipient_org, comment=comment)
    #Print confirmation
    if org:
        sender = f"`{org}`"
    else:
        sender = f"{interaction.user.mention}"

    if recipient_org:
        recipient = f"`{recipient_org}`"
    else:
        recipient = f"{recipient_user.mention}"

    if comment:
        comment = f" with comment:\n{comment}"
    else:
        comment = "."

    await interaction.response.send_message (f"Sent {amount:.2f}{currency} from {sender} to {recipient}{comment}")

    db.commit ()

class requestCategories(str, enum.Enum):
    Help = "help",
    Manual = "manual",
    CreateOrg = "create org",
    TransferOrg = "transfer org",
    DeleteOrg = "delete org"
    
@tree.command (name = "request", description = "Send a request to the bank administration", guild = guild)
@app_commands.choices(category=[
    app_commands.Choice(name="Create organisation", value="org.create"),
    app_commands.Choice(name="Transfer organisation", value="org.transfer"),
    app_commands.Choice(name="Delete organisation", value="org.delete"),
    app_commands.Choice(name="Other", value="other")
])
@app_commands.describe (
    category = "The general type of request you wish to make.",
    name = "Name of organisation",
    description = "(Partially optional) Description of organisation",
    comment = "Optional comment/message. You may go into detail on your request here"
)
#General-purpose function to send requests to the bank administration /Retha
async def request (interaction: discord.Interaction, category: requestCategories, name: str = "", description: str = "", comment: str = "")
    if db.getFlag("request", False) == "disable":
        await interaction.response.send_message ("This feature has been disabled.", ephemeral=True)
        return
    validOrgTypes = [requestCategories.CreateOrg, requestCategories.TransferOrg, requestCategories.DeleteOrg]
    validTypesHelp = {
        "Help": "Does NOT send anything to the bank administration, but gives information about the other request categories.\nBased on the fact you're reading this you've likely figured this category out, so good job! ɖː",
        "Manual": "Sends an unfiltered request to the bank administration, without any guardrails which the other request types have.\nUseful for special requests or suggestions which may not fit in any other categories.",
        "CreateOrg": "Sends a request to the bank administration to open an account in your name with the specified name & description.\nRequires both the name & description argument filled in.",
        "TransferOrg": "Sends a request to the bank administration to transfer one of your account(s) with the specified name to the specified person in the description (user ID is heavily recommended).\nRequires both the name & description argument filled in.",
        "DeleteOrg": "Sends a request to the bank administration to delete one of your account(s) with the specified name.\nRequires the name argument filled in."
    }

    if category == requestCategories.Help:
        if not description:
            await interaction.response.send_message ("Type in a request category into the description argument for relevant information.", ephemeral=True)
        elif description in validTypesHelp:
            await interaction.response.send_message (f"Category {description}:\n{validTypesHelp[description]}")
        else:
            await interaction.response.send_message (f"{description} is not a valid category. Please input the category as it is written in the category argument.")
        return

    #Will continue work after lunch; commiting for now. /Retha

@client.event
async def on_ready():
    await tree.sync (guild = guild)
    print("Ready!")

client.run (os.getenv("TOKEN"))
