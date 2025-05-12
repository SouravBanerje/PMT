import pymysql.cursors
from flask import g 
import os
from dotenv import load_dotenv



# Read database config from environment
DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')


# Helper function to get database connection
def get_db_connection():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        db=DB_NAME,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

def get_db():
    if 'db' not in g:
        g.db = get_db_connection()
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()