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
    name = db.truncate (org)

    #Make sure user exists
    db.ensureUserExists (interaction.user.id)

    if name:
        if not name in db.getUserOrgs(interaction.user.id).keys():
            await interaction.response.send_message (f"You are not the owner of `{name}`!", ephemeral=True)
        else:
            balance = db.getOrgBalance (name)
            await interaction.response.send_message (f"The account `{name}` has {balance:.2f}{currency}.", ephemeral=True)
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
    await pay (interaction, org, None, db.truncate (recipient), amount, comment)

#General-purpose function to perform a transaction with
async def pay (interaction, org, recipient_user, recipient_org, amount, comment):
    db.commit ()
    name = db.truncate (org)

    #Make sure sender exists
    db.ensureUserExists (interaction.user.id)

    #Round amount to send to two decimal places and verify it is valid
    amount = decimal.Decimal (amount).quantize (decimal.Decimal ("0.01"))
    if amount < 0:
        await interaction.response.send_message (f"You cannot send a negative amount of money", ephemeral=True)
    else:
        if not (recipient_user or recipient_org):
            raise Exception("Either recipient_user or recipient_org needs to be specified.")

        #Make sure recipient exists
        if recipient_user:
            db.ensureUserExists (recipient_user.id)
        if recipient_org and not recipient_org in db.getAllOrgs().keys():
            await interaction.response.send_message (f"Organisation `{recipient_org}` does not exist.", ephemeral=True)
        else:
            #Check that the sender owns the potential sender org
            if name and not name in db.getUserOrgs(interaction.user.id).keys():
                await interaction.response.send_message (f"You are not the owner of `{name}`!", ephemeral=True)
            else:
                #Check that the sender has enough money
                if name:
                    funds = db.getOrgBalance (name)
                else:
                    funds = db.getBalance (interaction.user.id)

                if amount <= funds:
                    #Set recipient id variable
                    if recipient_user:
                        recipient_id = recipient_user.id
                    else:
                        recipient_id = None

                    #Transfer money
                    db.transferMoney (amount, interaction.user.id, name, recipient_id, recipient_org, comment=comment)
                    if recipient_user:
                        await interaction.response.send_message (f"Sent {amount:.2f}{currency} from {interaction.user.mention} to {recipient_user.mention} with comment:\n{comment}")
                    else:
                        await interaction.response.send_message (f"Sent {amount:.2f}{currency} from {interaction.user.mention} to `{recipient_org}` with comment:\n{comment}")
                else:
                    await interaction.response.send_message (f"Insufficient balance, the selected account currently has {funds:.2f}{currency} left.", ephemeral=True)

    db.commit ()



@client.event
async def on_ready():
    await tree.sync (guild = guild)
    print("Ready!")

client.run (os.getenv("TOKEN"))
