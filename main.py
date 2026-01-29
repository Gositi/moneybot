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
guild = discord.Object (id = int (os.getenv ("GUILD")))

#Set currency symbol
currency = os.getenv ("CURRENCY")

#Get your own balance
@tree.command (name = "bal", description = "Get your balance", guild = guild)
async def bal (interaction: discord.Interaction):
    db.commit ()

    #Make sure user exists
    db.ensureUserExists (interaction.user.id)
    #Respond with balance
    await interaction.response.send_message (f"You have {db.getBalance (interaction.user.id):.2f}{currency}.", ephemeral=True)

    db.commit ()

#Pay/transfer money to someone else
@tree.command (name = "pay", description = "Transfer money", guild = guild)
@app_commands.describe (
    recipient = "Recipient of transfer",
    amount = "Amount of money to transfer, up to two decimal places",
    comment = "Optional transaction comment/message"
)
async def pay (interaction: discord.Interaction, recipient: discord.User, amount: float, comment: str = ""):
    db.commit ()

    #Make sure sender exists
    db.ensureUserExists (interaction.user.id)

    #Round amount to send to two decimal places and verify it is valid
    amount = decimal.Decimal (amount).quantize (decimal.Decimal ("0.01"))
    if amount < 0:
        await interaction.response.send_message (f"You cannot send a negative amount of money", ephemeral=True)
    else:
        #Make sure recipient exists
        db.ensureUserExists (recipient.id)

        #Check that the sender has enough money
        funds = db.getBalance (interaction.user.id)
        if amount <= funds:
            #Transfer money
            db.transferMoney (interaction.user.id, recipient.id, amount, comment=comment)
            await interaction.response.send_message (f"Sent {amount:.2f}{currency} from {interaction.user.mention} to {recipient.mention} with comment:\n{comment}")
        else:
            await interaction.response.send_message (f"Insufficient balance, you currently have {funds:.2f}{currency} left.", ephemeral=True)

    db.commit ()

@client.event
async def on_ready():
    await tree.sync (guild = guild)
    print("Ready!")

client.run (os.getenv("TOKEN"))
