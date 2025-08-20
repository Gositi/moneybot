#!/usr/bin/env python3

# Module Imports
import mariadb
import sys
import discord

#--------------------------------------------------------------
#------------------------------Setup---------------------------
#--------------------------------------------------------------

#Connect to database
try:
    conn = mariadb.connect(
        user="moneybot",
        password="gositi07",
        host="localhost",
        database="money"

    )
except mariadb.Error as e:
    print(f"Error connecting to MariaDB Platform: {e}")
    sys.exit(1)

#Set/get database cursor
cur = conn.cursor()

#Start discord.py and enable connection
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
token = "OTExMjAyNTEwOTczMzA4OTI5.YZd9dw.8dubcA2ETydjOVKbv0C_oUmUH4w"

#--------------------------------------------------------------
#------------------------------MariaDB-------------------------
#--------------------------------------------------------------

def showBalances ():
    cur.execute ("SELECT * FROM balances")

    for userID, balance in cur:
        print (userID, float (balance))

    conn.commit ()

def getBalance (userID):
    cur.execute ("SELECT balance FROM balances WHERE userID=?", (userID,))
    for balance in cur:
        return float (balance [0])
    
    conn.commit ()

def setBalance (userID, balance):
    cur.execute ("UPDATE balances SET balance=? WHERE userID=?", (balance, userID,))
    
    conn.commit ()

def changeBalance (userID, amount):
    setBalance (userID, getBalance (userID) + amount)
    
    conn.commit ()

def userExists (userID):
    cur.execute ("SELECT userID FROM balances WHERE userID=?", (userID,))
    for userID in cur:
        if userID != None:
            return True
        else:
            return False
    
    conn.commit ()

def addUser (userID):
    cur.execute ("INSERT INTO balances (userID, balance) VALUES (?, ?)", (userID, 50,))

    conn.commit ()

#--------------------------------------------------------------
#------------------------------Discord.py----------------------
#--------------------------------------------------------------

@client.event
async def on_message (message):
    #Check if it is a bot command
    if message.content [:3] == "mb." and message.content [3:6] in ["bal", "giv"]:
        print (message.content)

        #Get balance
        if message.content [3:6] == "bal":
            if not userExists (message.author.id):
                addUser (message.author.id)
            await message.reply (getBalance (message.author.id))

        #Give money
        elif message.content [3:6] == "giv":
            try:
                amount = abs (float (message.content.split () [-1]))
            except ValueError:
                await message.reply ("Invalid coins value")
                return

            receiver = message.mentions [0].id
            author = message.author.id
            
            if not userExists (author):
                addUser (author)

            if userExists (receiver):
                if amount <= getBalance (author):
                    changeBalance (author, -amount)
                    changeBalance (receiver, amount)
                    await message.reply ("Sent coins.")
                else:
                    await message.reply ("Insufficient balance.")
            else:
                await message.reply ("Invalid receiver")

@client.event
async def on_ready ():
    print ("Ready")

client.run (token)
