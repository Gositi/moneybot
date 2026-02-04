# moneybot
A discord bot for handling a virtual currency

## Usage
To use the bot, do the following:
- Create bot users
- Create database
- Fill in `.env` file
- Run the bot

### Create bot users
To do this, we refer to the Discord Developer portal.
The important thing is that the users (one regular and one admin) has `application.commands` permission.

### Create database
This program is made to be used with a `mariadb` (or `mysql`, probably)  database.
The database schema is as follows.

`balances`:
```
+---------+---------------+------+-----+---------+-------+
| Field   | Type          | Null | Key | Default | Extra |
+---------+---------------+------+-----+---------+-------+
| user_id | bigint(20)    | NO   | PRI | NULL    |       |
| balance | decimal(20,2) | NO   |     | 0.00    |       |
+---------+---------------+------+-----+---------+-------+
```

`transaction_log`:
```
+--------------+---------------+------+-----+---------------------+-------+
| Field        | Type          | Null | Key | Default             | Extra |
+--------------+---------------+------+-----+---------------------+-------+
| time         | timestamp     | YES  |     | current_timestamp() |       |
| sender_id    | bigint(20)    | YES  |     | NULL                |       |
| recipient_id | bigint(20)    | YES  |     | NULL                |       |
| amount       | decimal(20,2) | YES  |     | NULL                |       |
| comment      | tinytext      | YES  |     | NULL                |       |
+--------------+---------------+------+-----+---------------------+-------+
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

## Legal
Copyright (C) 2025-2026 Gositi

License (GPL 3.0) provided in file `LICENSE`

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU General Public License for more details.
