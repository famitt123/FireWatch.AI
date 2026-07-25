import pandas as pd

df = pd.read_csv("cwfif_Ontario_activefires.csv")

print(f"Total rows: {len(df)}")
print(df[["region_code", "agency_fire_id", "fire_size", "stage_of_control_status", "latitude", "longitude"]].head())

import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="firewatch",
    user="firewatch",
    password="devpassword"
)
cursor = conn.cursor()

# Build a lookup: region_code -> region_id, from the regions table
cursor.execute("SELECT name, id FROM regions;")
region_lookup = dict(cursor.fetchall())

print(region_lookup)

status_map = {
    "OC": "out of control",
    "BH": "being held",
    "UC": "under control",
    "MON": "being monitored"
}

inserted = 0
for _, row in df.iterrows():
    region_id = region_lookup.get(row["region_code"])
    if region_id is None:
        print(f"Skipping {row['agency_fire_id']} - unknown region {row['region_code']}")
        continue

    status = status_map.get(row["stage_of_control_status"], row["stage_of_control_status"])

    cursor.execute(
        """
        INSERT INTO fire_incidents (region_id, fire_number, status, size_hectares, location)
        VALUES (%s, %s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326))
        """,
        (region_id, row["agency_fire_id"], status, row["fire_size"], row["longitude"], row["latitude"])
    )
    inserted += 1

conn.commit()
cursor.close()
conn.close()
print(f"Inserted {inserted} fires")