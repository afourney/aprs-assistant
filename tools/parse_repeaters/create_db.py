import sqlite3
import io
import sys
import json

# Define the database filename and data files
db_filename = "repeaters.db"
json_filename = "repeaters.json"

# SQL query to create the "EN" table
create_table_query = """  
CREATE TABLE IF NOT EXISTS Repeaters (  
    id INT PRIMARY KEY,
    callsign TEXT,
    latitude REAL,
    longitude REAL,
    city TEXT,
    category TEXT,
    internet_node TEXT,
    mode TEXT,
    encode TEXT,
    decode TEXT,
    frequency BIGINT,
    offset BIGINT,
    description TEXT,
    power TEXT,
    operational BOOLEAN,
    restriction TEXT
);  
"""

create_callsign_index = "CREATE INDEX callsign_index ON Repeaters (callsign);"
create_mode_index = "CREATE INDEX mode_index ON Repeaters (mode);"
create_lat_lon_index = "CREATE INDEX lat_lon_index ON Repeaters (latitude, longitude);"

# Connect to the SQLite database
conn = sqlite3.connect(db_filename)
cursor = conn.cursor()

# Create the "EN" table
cursor.execute(create_table_query)
cursor.execute(create_callsign_index)
cursor.execute(create_mode_index)
cursor.execute(create_lat_lon_index)


def _strip(s):
    if s is not None:
        return s.strip()
    return None


def _upper(s):
    if s is not None:
        return s.strip().upper()
    return None


# Function to insert records into the Repeater table
def insert_repeater_record(record):
    insert_query = """  
    INSERT INTO Repeaters (  
        id,
        callsign,
        latitude,
        longitude,
        city,
        category,
        internet_node,
        mode,
        encode,
        decode,
        frequency,
        offset,
        description,
        power,
        operational,
        restriction
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);  
    """
    cursor.execute(
        insert_query,
        (
            record["id"],
            _upper(record["callsign"]),
            record["latitude"],
            record["longitude"],
            _strip(record["city"]),
            _upper(record["group"]),
            _strip(record["internet_node"]),
            _upper(record["mode"]),
            _strip(record["encode"]),
            _strip(record["decode"]),
            record["frequency"],
            record["offset"],
            _strip(record["description"]),
            _strip(record["power"]),
            record["operational"],
            _strip(record["restriction"]),
        ),
    )


with open(json_filename, "rt") as fh:
    data = json.loads(fh.read())
    for record in data:
        insert_repeater_record(record)

# Commit the transaction and close the connection
conn.commit()
conn.close()
