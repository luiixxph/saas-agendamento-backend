import os
import psycopg2
from psycopg2 import pool
from dotenv import load_dotenv

load_dotenv()

connection_pool = psycopg2.pool.SimpleConnectionPool(1, 10, dsn=os.getenv("DATABASE_URL"))


def get_connection():
    return connection_pool.getconn()


def release_connection(conn):
    connection_pool.putconn(conn)
