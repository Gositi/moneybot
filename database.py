#!/usr/bin/env python3

#Moneybot, a discord bot for handling a virtual currency
#Copyright (C) 2025-2026 Gositi
#License (GPL 3.0) provided in file 'LICENSE'

#MariaDB
import mariadb
#Decimal numbers for currencies
import decimal

class Database:
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
            raise (f"Error connecting to MariaDB database: {e}")

        #Get cursor to execute SQL commands
        self.cur = self.conn.cursor ()

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
    def transferMoney (self, sender, recipient, amount, logging=True, comment=""):
        self.changeBalance (sender, -amount)
        self.changeBalance (recipient, amount)
        if logging:
            self.logTransaction (sender, recipient, amount, comment=comment)

    #Log a transaction
    def logTransaction (self, sender, recipient, amount, comment=""):
        self.cur.execute ("INSERT INTO transaction_log (sender_id, recipient_id, amount, comment) VALUES (?, ?, ?, ?)", (sender, recipient, amount, comment,))

    #Make sure user exists
    def ensureUserExists (self, user):
        self.cur.execute ("INSERT IGNORE INTO balances (user_id, balance) VALUES (?, ?)", (user, 0,))

