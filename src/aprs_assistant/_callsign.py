# SPDX-FileCopyrightText: 2024-present Adam Fourney <adam.fourney@gmail.com>
#
# SPDX-License-Identifier: MIT
import requests
import json
import os
import re
import sqlite3
import maidenhead

from ._cache import read_cache, write_cache
from ._constants import FCC_DATABASE, SECONDS_IN_MINUTE, USER_AGENT
from ._itu_prefixes import ITU_CALLSIGN_PREFIXES
from ._location import geocode

FCC_CLASS_CODES = {
    "A": "Advanced",       			
    "E": "Amateur Extra",  			
    "G": "General",			
    "N": "Novice",      			
    "P": "Technician Plus",		
    "T": "Technician",
}

def get_callsign_info(callsign, include_address=True):
    
    fcc_record = fcc_callsign_lookup(callsign)
    if fcc_record is None:
        fcc_record = fcc_callsign_lookup(callsign.split("-")[0])

    if fcc_record:
        _type = "Amateur Radio" if fcc_record["Service"] == "AMAT" else fcc_record["Service"]
        _class = FCC_CLASS_CODES.get(fcc_record["Operator_Class"], "N/A")
        _zip = fcc_record["Zip_Code"][0:5] if len(fcc_record["Zip_Code"]) > 5 else fcc_record["Zip_Code"]
        
        # Pretty-print the name
        name = fcc_record["First_Name"] + " " + fcc_record["Middle_Initial"] + " " + fcc_record["Last_Name"]
        name = re.sub(r"\s+", " ", name.strip())
        if name == "":
            name = fcc_record["Entity_Name"]  

        if fcc_record["Service"] == "GMRS":
            name += " (and immediate family)"

        result = f"# FCC {_type} License Record"
        result += "\n" + ("="*len(result)) + "\n"
        result += f"Call Sign: {fcc_record['Call_Sign']}\n" 
        result += f"Name: {name}\n" 
        
        if fcc_record["Service"] != "GMRS":
            result += f"Class: {_class}\n\n" 

        if include_address:
            result += "Station Addess at Time of Licensing (May be outdated!):\n\n"
            result += f"    {fcc_record['Street_Address']}\n"
            result += f"    {fcc_record['City']}\n"
            result += f"    {fcc_record['State']}, USA\n"
            result += f"    {_zip}\n"

            geo = geocode(
                street=fcc_record["Street_Address"], 
                city=fcc_record["City"],
                state=fcc_record["State"],
                country="USA",
                postalcode=_zip)

            if geo:
                gridsquare = maidenhead.to_maiden(float(geo['lat']), float(geo['lon']))
                result += f"\n    Latitude: {geo['lat']}\n"
                result += f"    Longitude: {geo['lon']}\n"
                result += f"    Maidenhead Grid Square: {gridsquare}\n"

        return result

    # No FCC record, but what else can we find?
    itu_country = itu_prefix_lookup(callsign)
    if itu_country:
        return f"No information about {callsign}, but the call sign was likely issued by {itu_country}."

    return None


def itu_prefix_lookup(callsign):
    callsign = callsign.strip().upper()
    for prefix in ITU_CALLSIGN_PREFIXES:
        if callsign.startswith(prefix[0]):
            return prefix[1]
    return None


def fcc_callsign_lookup(callsign):

    # Database not found
    if not os.path.isfile(FCC_DATABASE):
        return None

    # Connect to the SQLite database
    conn = sqlite3.connect(FCC_DATABASE)
    cursor = conn.cursor()

    # SQL query to select a row with the given call sign
    cursor.execute("""SELECT 
    Service,
    Unique_System_Identifier,
    ULS_File_Number,
    Call_Sign,
    Entity_Type,
    Entity_Name,
    First_Name,
    Middle_Initial,
    Last_Name,
    Street_Address,
    City,
    State,
    Zip_Code,
    Status_Code,
    Status_Date,
    Linked_Call_Sign,
    Operator_Class,
    Group_Code,
    Region_Code
FROM CallSignView WHERE Call_Sign = ?;""", (callsign,))
    row = cursor.fetchone()

    # Check if a matching row was found and print it
    result = None
    if row:
        result = {
            "Service": row[0],
            "Unique_System_Identifier": row[1],
            "ULS_File_Number": row[2],
            "Call_Sign": row[3],
            "Entity_Type": row[4],
            "Entity_Name": row[5],
            "First_Name": row[6],
            "Middle_Initial": row[7],
            "Last_Name": row[8],
            "Street_Address": row[9],
            "City": row[10],
            "State": row[11],
            "Zip_Code": row[12],
            "Status_Code": row[13],
            "Status_Date": row[14],
            "Linked_Call_Sign": row[15],
            "Operator_Class": row[16],
            "Group_Code": row[17],
            "Region_Code": row[18],
        }

    conn.close()
    return result
