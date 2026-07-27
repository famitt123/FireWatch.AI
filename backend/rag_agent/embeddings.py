# Reads every generated fire sentence and converts it into a vector using Ollama's local embedding model, so the chatbot can later search by meaning
import psycopg2
import requests

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="firewatch",
    user="firewatch",
    password="devpassword"
)
cursor = conn.cursor()

# Get every generated fire document so we can turn each one into a searchable vector
cursor.execute("SELECT id, raw_text FROM fire_documents;")
documents = cursor.fetchall()

inserted = 0
for doc_id, text in documents:
    # Ask Ollama's local embedding model (running on port 11434) to convert this sentence into a vector
    response = requests.post(
        "http://localhost:11434/api/embeddings",
        json={"model": "nomic-embed-text", "prompt": text}
    )
    embedding = response.json()["embedding"]  # pull the actual vector out of Ollama's response

    cursor.execute(
        "INSERT INTO document_embeddings (document_id, embedding, chunk_text) VALUES (%s, %s, %s)",
        (doc_id, embedding, text)
    )  # save the vector alongside the original text, so we can show the real sentence once it's retrieved later
    inserted += 1
    print(f"Embedded {inserted}/{len(documents)}")  # shows real progress instead of silence, since 169 calls takes a while

conn.commit()
cursor.close()
conn.close()
print(f"Generated {inserted} embeddings")