# db.py
import psycopg2
import json
import os
import dotenv
from dotenv import load_dotenv


# Load .env
load_dotenv()

USER = os.getenv("user")
PASSWORD = os.getenv("password")
HOST = os.getenv("host")
PORT = os.getenv("port")
DBNAME = os.getenv("dbname")


def get_db_connection():
    
    try:
        connection = psycopg2.connect(
            user=USER,
            password=PASSWORD,
            host=HOST,
            port=PORT,
            dbname=DBNAME
        )
        print("Connection successful!")
        
        # connection.close()
        # print("Connection closed.")

    except Exception as e:
        print(f"Failed to connect: {e}")

    return connection 

    

# Fetch past questions for a user and topic
def get_past_questions(user_id: str, topic: str) -> list:
    try:
        user_id = int(user_id)
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT q.question 
            FROM questions q
            JOIN quizzes z ON q.quiz_id = z.id
            WHERE z.user_id = %s AND LOWER(z.quiz_name) = LOWER(%s)
            """,
            (user_id, topic)
        )
        past_questions = [row[0] for row in cur.fetchall()]
        cur.close()
        conn.close()
        print("past_questions :\n",past_questions)
        return past_questions
    except Exception as e:
        print(f"Failed to fetch past questions for the user : {user_id} and topic :{topic} . ERROR : {e}")
