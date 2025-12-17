import pymysql
from dotenv import load_dotenv
import os

load_dotenv()

def get_db():
    return pymysql.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", 4000)),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "pokefarm"),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor
    )