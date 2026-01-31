# moneybot
A discord bot for handling a virtual currency

## Usage
To use the bot, do the following:
- Create bot users
- Create database
- Fill in `.env` file
- Run the bot

### Create bot users
To do this, we refer to the Discord Developer portal

### Create database
This program is made to be used with a `mariadb` database.
The database schema is:
```
MariaDB [moneybot]> show tables;
+--------------------+
| Tables_in_moneybot |
+--------------------+
| balances           |
| transactionLog     |
+--------------------+
2 rows in set (0.001 sec)

MariaDB [moneybot]> desc balances;
+---------+---------------+------+-----+---------+-------+
| Field   | Type          | Null | Key | Default | Extra |
+---------+---------------+------+-----+---------+-------+
| userID  | bigint(20)    | NO   | PRI | NULL    |       |
| balance | decimal(20,2) | YES  |     | NULL    |       |
+---------+---------------+------+-----+---------+-------+
2 rows in set (0.001 sec)

MariaDB [moneybot]> desc transactionLog;
+-------------+---------------+------+-----+---------------------+-------+
| Field       | Type          | Null | Key | Default             | Extra |
+-------------+---------------+------+-----+---------------------+-------+
| time        | timestamp     | YES  |     | current_timestamp() |       |
| senderID    | bigint(20)    | YES  |     | NULL                |       |
| recipientID | bigint(20)    | YES  |     | NULL                |       |
| amount      | decimal(20,2) | YES  |     | NULL                |       |
| comment     | tinytext      | YES  |     | NULL                |       |
+-------------+---------------+------+-----+---------------------+-------+
5 rows in set (0.001 sec)

MariaDB [moneybot]>
```

You also need to setup a connection between Python and MariaDB.
To do this you'll need (on Ubuntu) the `mariadb-server` and `libmariadb-dev` apt packages, and the `mariadb` Python package.

### Fill in the `.env` file
Your `.env` file should look like the following:
```
DB_USER="name of database user"
DB_PASS="password of database user"
TOKEN="token of non-admin bot"
GUILD="main server ID of non-admin bot"
ADMIN_TOKEN="token of admin bot"
ADMIN_GUILD="main server ID of admin bot"
CURRENCY="name/symbol of currency"
```

### Run the bot
To run the main bot execute `main.py`, to run the admin bot execute `admin.py`.
