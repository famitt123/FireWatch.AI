# Turns real structured fire data (status, size, region) into real descriptive sentences, since CWFIS gives numbers/codes, not narrative text needed for RAG
import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="firewatch",
    user="firewatch",
    password="devpassword"
)
cursor = conn.cursor()

# Pull real fire data, joined with region names, to generate real descriptive sentences
cursor.execute("""
    SELECT f.id, f.fire_number, f.status, f.size_hectares, r.name
    FROM fire_incidents f
    JOIN regions r ON f.region_id = r.id;
""")
fires = cursor.fetchall()

inserted = 0
for fire_id, fire_number, status, size, region in fires:
    text = f"Fire {fire_number} near {region}, Ontario is currently {status}, burning {size} hectares." # builds one honest sentence per real fire
    cursor.execute(
        "INSERT INTO fire_documents (fire_id, raw_text, source_url) VALUES (%s, %s, %s)",
        (fire_id, text, "generated from CWFIS structured data")
    )
    inserted += 1

print(f"Generated {inserted} fire documents")

# Pull real air quality readings, joined with region names, to generate real descriptive sentences too
cursor.execute("""
    SELECT a.id, r.name, a.aqhi
    FROM air_quality_readings a
    JOIN regions r ON a.region_id = r.id;
""")
readings = cursor.fetchall()

aq_inserted = 0
for reading_id, region, aqhi in readings:
    text = f"Air quality in {region}, Ontario currently has an AQHI of {aqhi}." # builds one honest sentence per real air quality reading
    cursor.execute(
        "INSERT INTO fire_documents (fire_id, raw_text, source_url) VALUES (%s, %s, %s)",
        (None, text, "generated from Air Quality Ontario data") # fire_id is None since this isn't tied to a specific fire
    )
    aq_inserted += 1

print(f"Generated {aq_inserted} air quality documents")

conn.commit()
cursor.close()
conn.close()
print(f"Generated {inserted + aq_inserted} total documents")