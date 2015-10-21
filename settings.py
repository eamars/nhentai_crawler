__author__ = 'Ran Bao'

# Specify the number of worker threads
NUM_WORKERS = 10

# Database name in MySQL database
DB_NAME = "nhentai"

# Table name in MySQL database
TABLE_NAME = "downloaded"

# Specify how long the program should wait when network error occurs
BACKOFF_TIMER = 5

# Connection configuration for MySQL Connection
SQL_CONFIG = {
    "host": "localhost",
    "user": "username",
    "password": "password",
    "autocommit": True
}