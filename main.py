#!/usr/bin/env python3

#MariaDB
import mariadb
#Discord
import discord
from discord import app_commands
#Dotenc
from dotenv import load_dotenv
import os
#Decimal numbers for currencies
import decimal

#
#   Setup
#

load_dotenv ()
decimal.getcontext ().prec = 2

#Connect to database
try:
    conn = mariadb.connect(
        user="simon",
        password=os.getenv("DB_PASS"),
        host="localhost",
        database="moneybot"

    )
except mariadb.Error as e:
    print(f"Error connecting to MariaDB Platform: {e}")
    sys.exit(1)

#Set/get database cursor
cur = conn.cursor()

#Setup Discord bot
intents = discord.Intents.default ()
client = discord.Client (intents=intents)
tree = app_commands.CommandTree (client)
guild = discord.Object (id = int (os.getenv ("GUILD_ID")))

#
#   MariaDB
#

def commit ():
    conn.commit ()

def getBalance (userID):
    cur.execute ("SELECT balance FROM balances WHERE userID=?", (userID,))
    for balance in cur:
        return decimal.Decimal (balance [0])

def setBalance (userID, balance):
    cur.execute ("UPDATE balances SET balance=? WHERE userID=?", (balance, userID,))

def changeBalance (userID, amount):
    setBalance (userID, decimal.Decimal (getBalance (userID)) + amount)

def userExists (userID):
    cur.execute ("SELECT userID FROM balances WHERE userID=?", (userID,))
    for userID in cur:
        if userID != None:
            return True
        else:
            return False

def addUser (userID):
    cur.execute ("INSERT INTO balances (userID, balance) VALUES (?, ?)", (userID, 0,))

#
#   Discord
#

@tree.command (name = "bal", description = "Get your balance", guild = guild)
async def bal (interaction: discord.Interaction):
    commit ()

    #Make sure user exists
    if not userExists (interaction.user.id):
        addUser (interaction.user.id)
    #Respond with balance
    await interaction.response.send_message (f"You have {getBalance (interaction.user.id):.2f} money.", ephemeral=True)

    commit ()

@tree.command (name = "pay", description = "Transfer money", guild = guild)
@app_commands.describe (
    recipient = "Recipient of transfer",
    amount = "Amount of money to transfer, up to two decimal places",
    comment = "Optional transaction comment/message"
)
async def pay (interaction: discord.Interaction, recipient: discord.Member, amount: float, comment: str):
    commit ()

    #Make sure sender exists
    if not userExists (interaction.user.id):
        addUser (interaction.user.id)

    #Round amount to send to two decimal places and verify it is valid
    amount = decimal.Decimal (amount)
    if amount < 0:
        await interaction.response.send_message (f"You cannot send a negative amount of money", ephemeral=True)
    else:
        #Make sure recipient exists
        if not userExists (recipient.id):
            addUser (recipient.id)

        #Check that the sender has enough money
        funds = getBalance (interaction.user.id)
        if amount <= funds:
            #Transfer money
            changeBalance (interaction.user.id, -amount)
            changeBalance (recipient.id, amount)
            await interaction.response.send_message (f"Sent {amount:.2f} from {interaction.user.mention} to {recipient.mention} with comment:\n{comment}")
        else:
            await interaction.response.send_message (f"Insufficient balance, you currently have {funds:.2f} money left.", ephemeral=True)

    commit ()

@client.event
async def on_ready():
    await tree.sync (guild = guild)
    print("Ready!")

client.run (os.getenv("TOKEN"))
