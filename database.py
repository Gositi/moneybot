#!/usr/bin/env python3

#Moneybot, a discord bot for handling a virtual currency
#Copyright (C) 2025-2026 Gositi, Retha
#License (GPL 3.0) provided in file 'LICENSE'

#MariaDB
import mariadb
#Decimal numbers for currencies
import decimal

class Database:
    featureFlags = {"request": "disable"} #I still need
    def __init__ (self, user, host, passwd, database):
        #Connect to database
        try:
            self.conn = mariadb.connect (
                user = user,
                host = host,
                passwd = passwd,
                database = database,
                init_command = "SET SESSION wait_timeout = 86400"
            )
        except mariadb.Error as e:
            raise RuntimeError(f"Error connecting to MariaDB database: {e}")

        #Get cursor to execute SQL commands
        self.cur = self.conn.cursor ()

    #Truncate the name of an organisation account
    def truncate (self, name):
        return name[:5]

    #Commit commands issued
    def commit (self):
        self.conn.commit ()

    #Get balance of user
    def getBalance (self, user):
        self.cur.execute ("SELECT balance FROM balances WHERE user_id=?", (user,))
        for balance in self.cur:
            return decimal.Decimal (balance [0])

    #Get balance of every user
    def getBalances (self):
        self.cur.execute ("SELECT user_id, balance FROM balances")
        return {user_id: balance for user_id, balance in self.cur}

    #Set balance of user
    def setBalance (self, user, balance):
        self.cur.execute ("UPDATE balances SET balance=? WHERE user_id=?", (balance, user,))

    #Change balance of user by amount
    def changeBalance (self, user, amount):
        self.setBalance (user, self.getBalance (user) + amount)

    #Transfer amount money from sender to recipient
    def transferMoney (self, amount, sender_id, sender_org=None, recipient_id=None, recipient_org=None, logging=True, comment=""):
        if not (recipient_id or recipient_org):
            raise Exception("recipient_id or recipient_org must be defined")

        if sender_org:
            self.changeOrgBalance (sender_org, -amount)
        else:
            self.changeBalance (sender_id, -amount)

        if recipient_org:
            self.changeOrgBalance (recipient_org, amount)
        else:
            self.changeBalance (recipient_id, amount)

        if logging:
            self.logTransaction (amount, sender_id=sender_id, sender_org=sender_org, recipient_id=recipient_id, recipient_org=recipient_org, comment=comment)

    #Log a transaction
    def logTransaction (self, amount, sender_id=None, sender_org=None, recipient_id=None, recipient_org=None, comment=""):
        self.cur.execute ("INSERT INTO transaction_log (sender_id, sender_org, recipient_id, recipient_org, amount, comment) VALUES (?, ?, ?, ?, ?, ?)", (sender_id, sender_org, recipient_id, recipient_org, amount, comment,))

    #Make sure user exists
    def ensureUserExists (self, user):
        self.cur.execute ("INSERT IGNORE INTO balances (user_id) VALUES (?)", (user,))

    #Create organisation account
    def createOrgAcc (self, user, name, description=""):
        self.cur.execute ("INSERT IGNORE INTO org_balances (org_name, user_id, description) VALUES (?, ?, ?)", (name, user, description,))

    #Delete organisation account
    def deleteOrgAcc (self, name):
        self.cur.execute ("DELETE FROM org_balances WHERE org_name=?", (name,))

    #Get info about every org
    def getAllOrgs (self):
        self.cur.execute ("SELECT org_name, user_id, balance, description FROM org_balances")
        return {org_name: (user_id, balance, description) for org_name, user_id, balance, description in self.cur}

    #Get balance of org
    def getOrgBalance (self, name):
        self.cur.execute ("SELECT balance FROM org_balances WHERE org_name=?", (name,))
        for balance in self.cur:
            return decimal.Decimal (balance [0])

    #Set balance of org
    def setOrgBalance (self, name, balance):
        self.cur.execute ("UPDATE org_balances SET balance=? WHERE org_name=?", (balance, name,))

    #Change balance of org
    def changeOrgBalance (self, name, amount):
        self.setOrgBalance (name, self.getOrgBalance (name) + amount)

    #Change user of org
    def changeOrgOwner (self, name, user):
        self.cur.execute ("UPDATE org_balances SET user_id=? WHERE org_name=?", (user, name,))

    #Get every org owned by user
    def getUserOrgs (self, user):
        self.cur.execute ("SELECT org_name, balance, description FROM org_balances WHERE user_id=?", (user,))
        return {org_name: (balance, description) for org_name, balance, description in self.cur}

    #Gets if the user owns the org, or who owns the org if a user isn't passed /Retha
    def checkOrgOwner (self, org, user=None):
        owner = self.cur.execute("SELECT user_id FROM org_balances WHERE org_name=?", (org,))
        if not user:
            return owner
        return user == owner
        
    #Get info about everything, I hope. /Retha
    def getAllLogs (self, count, offset):
        self.cur.execute ("SELECT time, sender_id, sender_org, recipient_id, recipient_org, amount, comment FROM transaction_log ORDER BY time DESC OFFSET ? ROWS FETCH FIRST ? ROWS ONLY", (offset, count,))
        return {time: (sender_id, sender_org, recipient_id, recipient_org, amount, comment) for time, sender_id, sender_org, recipient_id, recipient_org, amount, comment in self.cur}

    #Surprisingly, this function adds a comment! /Retha
    def addComment (self, comment):
        self.cur.execute ("INSERT INTO transaction_log (comment) VALUES (?)", (comment,))

    #Appends a request to the request log. /Retha
    #This thing is not ready yet, I think I'll need some help making the requests differentiable when responding to them. :/  /Retha
    #def logRequest (self, sender_id=None, type, name=None, description="", comment=""):
        #self.cur.execute ("INSERT INTO request_log (request_id, sender_id, type, name, description, comment, response) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (sender_id, type, name, description, comment, "",))

    #Sets a feature flag to the specified value. /Retha
    def setFlag (self, flag, value=None):
        self.featureFlags[flag] = value

    #Gets the value of a feature flag. /Retha
    def getFlag (self, flag, forceBool: bool=None, defaultBool: bool=None):
        v = self.featureFlags[flag]
        #Conforms the flag value to whatever the calling function expects.
        if forceBool == True and v not in [True, False]:
            if v in ["enable", "True"]:
                v = True
            elif v in ["disable", "False"]:
                v = False
            else:
                v = defaultBool
        elif forceBool == False:
            if v == True:
                v = "enable"
            elif v == False:
                v = "disable"
        return v


    def replyRequest
