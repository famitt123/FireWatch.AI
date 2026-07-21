from fastapi import FastAPI
import psycopg2 # importing the psycopg2 library to let python send sql commands to Postgres

app = FastAPI()

# This function basically opens a live connection to Postgres using the correct address and login and gives that connection back to whoever asked for it.
# Basic clinet to server and server to clinet relationship :D
def get_connection():
    return psycopg2.connect(
        host="localhost",
        port=5432,
        database="firewatch",
        user="firewatch",
        password="devpassword"
    )

#Created an endpoint which connects to Postgres (Main database), runs a SELECT on fire_incidents relational model and returns the results as JSON
@app.get('/fires')
def get_fires():
    conn = get_connection()
    cursor = conn.cursor() # get a cursor to send SQL and read results
    cursor.execute("SELECT fire_number, status, size_hectares FROM fire_incidents;") # excutes the actual query that I have selected
    rows = cursor.fetchall() # This command fetches all of the data from the matching rows (like from the SELECT statement above :D) of the fire_incidents query
  
    # Convert each unlabeled database row into a labeled dictionary so the JSON output is clear
    fires = []
    for row in rows:
        fires.append({
            "fire_number": row[0],
            "status": row[1],
            "size_hectares": row[2]
        })
    cursor.close() # closes cursor to free up space on the server
    conn.close()  # closes connection completely
    return fires


@app.get('/')
def read_root():
    return {'message': 'FireWatch.AI backend server is Running :D'}