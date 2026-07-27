from fastapi import FastAPI
import psycopg2 # importing the psycopg2 library to let python send sql commands to Postgres
import requests

app = FastAPI()
from fastapi.middleware.cors import CORSMiddleware
# Allows the frontend (running on a different port) to fetch data from this backend — browsers block cross-origin requests by default unless explicitly permitted
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
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
    cursor.execute("""
        SELECT f.fire_number, f.status, f.size_hectares, r.name
        FROM fire_incidents f
        LEFT JOIN regions r ON f.region_id = r.id;
    """) # JOIN pulls in the readable region name alongside each fire, instead of just the raw code
    rows = cursor.fetchall() # This command fetches all of the data from the matching rows (like from the SELECT statement above :D) of the fire_incidents query

    # Convert each unlabeled database row into a labeled dictionary so the JSON output is clear
    fires = []
    for row in rows:
        fires.append({
            "fire_number": row[0],
            "status": row[1],
            "size_hectares": row[2],
            "region": row[3] # readable region name for display on the frontend
        })
    cursor.close() # closes cursor to free up space on the server
    conn.close()  # closes connection completely
    return fires
    
# Created an endpoint which connects to Postgres, runs a SELECT on the regions table, and returns the results as JSON
@app.get('/regions')
def get_regions():
    conn = get_connection()
    cursor = conn.cursor() # get a cursor to send SQL and read results
    cursor.execute("SELECT name FROM regions;") # grabs just the region names, nothing else needed here
    rows = cursor.fetchall() # fetches all matching rows from the regions table

    # Convert each unlabeled row into a labeled dictionary so the JSON output is clear
    regions = []
    for row in rows:
        regions.append({
            "name": row[0]
        })
    cursor.close() # closes cursor to free up space on the server
    conn.close()  # closes connection completely
    return regions

# Created an endpoint which joins air_quality_readings with regions, so the response shows a real region name instead of a raw UUID
@app.get('/air-quality')
def get_air_quality():
    conn = get_connection()
    cursor = conn.cursor() # get a cursor to send SQL and read results
    cursor.execute("""
        SELECT r.name, a.aqhi FROM air_quality_readings a
        JOIN regions r ON a.region_id = r.id;
    """) # JOIN pulls the readable region name in, matched by region_id
    rows = cursor.fetchall() # fetches all matching rows, one per station

    # Convert each unlabeled row into a labeled dictionary so the JSON output is clear
    air_quality = []
    for row in rows:
        air_quality.append({
            "region": row[0],
            "aqhi": row[1]
        })
    cursor.close() # closes cursor to free up space on the server
    conn.close()  # closes connection completely
    return air_quality

@app.get('/fires-geo')
def get_fires_geo():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT fire_number, status, size_hectares, ST_Y(location), ST_X(location) FROM fire_incidents WHERE location IS NOT NULL;")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [{"fire_number": r[0], "status": r[1], "size_hectares": r[2], "lat": r[3], "lng": r[4]} for r in rows]

# Takes a user's question, finds the most relevant real fire sentences using vector similarity, and asks Ollama to answer using only that real context
@app.get('/chat')
def chat(question: str):
    # Step 1: convert the question into a vector, using the same embedding model used to build document_embeddings
    embed_response = requests.post(
        "http://localhost:11434/api/embeddings",
        json={"model": "nomic-embed-text", "prompt": question}
    )
    question_vector = embed_response.json()["embedding"]

    # Step 2: find the 3 real fire sentences whose vectors are closest in meaning to the question
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT chunk_text FROM document_embeddings ORDER BY embedding <-> %s::vector LIMIT 3;",
        (question_vector,)
    )
    matches = cursor.fetchall()
    cursor.close()
    conn.close()

    context = "\n".join(row[0] for row in matches) # combine the 3 matched real sentences into one block of context

    # Step 3: ask Ollama's chat model to answer, using only the real retrieved sentences as grounding
    prompt = f"Using only this information, answer the question in one or two sentences:\n{context}\n\nQuestion: {question}"
    chat_response = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": "llama3.1:8b", "prompt": prompt, "stream": False}
    )
    answer = chat_response.json()["response"]

    return {"answer": answer, "sources": [row[0] for row in matches]}
    
@app.get('/')
def read_root():
    return {'message': 'FireWatch.AI backend server is Running :D'}