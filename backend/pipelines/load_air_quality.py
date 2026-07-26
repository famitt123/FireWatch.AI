import pandas as pd
import psycopg2
# Webscraping the data from Air Quality Ontario and inserting into Air_Quality_Readings relational table in the database

url = "https://www.airqualityontario.com/aqhi/locations.php?forecast_period=1&text_only=1"
tables = pd.read_html(url)
df = tables[0]

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="firewatch",
    user="firewatch",
    password="devpassword"
)
cursor = conn.cursor()

cursor.execute("SELECT name, id FROM regions;")
region_lookup = dict(cursor.fetchall())

inserted = 0
for _, row in df.iterrows():
    region_id = region_lookup.get(row["Station"])
    if region_id is None:
        print(f"Skipping {row['Station']} - no matching region")
        continue

    cursor.execute(
        "INSERT INTO air_quality_readings (region_id, aqhi) VALUES (%s, %s)",
        (region_id, row["AQHI"])
    )
    inserted += 1

conn.commit()
cursor.close()
conn.close()
print(f"Inserted {inserted} air quality readings")