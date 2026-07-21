from fastapi import FastAPI
import psycopg2 # importing the psycopg2 library to let python send sql commands to Postgres

app = FastAPI()

# This function basically opens a live connection to Postgres using the correct address and login, and gives that connection back to whoever asked for it.
# Basic clinet to server and server to clinet relationship :D
def get_connection():
    return psycopg2.connect(
        host="localhost",
        port=5432,
        database="firewatch",
        user="firewatch",
        password="devpassword"
    )

#Created an endpoint which connects to Postgres (Main database), runs a SELECT on fire_incidents and returns the results as JSON
@app.get('/fires')
def get_fires():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT fire_number, status, size_hectares FROM fire_incidents;")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows
    
@app.get('/')
def read_root():
    return {'message': 'FireWatch.AI backend server is Running :D'}