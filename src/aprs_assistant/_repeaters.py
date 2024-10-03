# SPDX-FileCopyrightText: 2024-present Adam Fourney <adam.fourney@gmail.com>
#
# SPDX-License-Identifier: MIT
import os
import sqlite3
import re
from haversine import haversine, inverse_haversine, Unit, Direction
from typing import NamedTuple

from ._constants import REPEATER_DATABASE

# Modes are regular expressions that are run against the 'mode' field in the database.
MODE_FM = r"^FM$"
MODE_DMR = r"DMR"
MODE_YSF = r"YSF"
MODE_D_STAR = r"D\-?STAR"

# Bands are lists of tuples, with each tuple indicating the lower and upper bounds of a frequency range.
BAND_2M = [(144, 148)]
BAND_1_25M = [(219, 225)]
BAND_70CM = [(420, 450)]
BAND_GMRS = [(462.5500, 462.7250), (467.5500, 467.7250)]


class Repeater(NamedTuple):
    id: int
    callsign: str
    latitude: float
    longitude: float
    city: str
    category: str
    internet_node: str
    mode: str
    encode: str
    decode: str
    frequency: int
    offset: int
    description: str
    power: str
    operational: bool
    restriction: str
    distance: float | None  # Added by search_repeaters_by_location


def _is_null_or_whitesace(s):
    if s is None:
        return True
    if isinstance(s, str) and s.strip() == "":
        return True
    return False


# Removes blank lines and runs of spaces
def _normalize_spaces(s):
    lines = re.split(r"[\n\r]+", s)
    lines = [re.sub(r"\s+", " ", l).strip() for l in lines]
    return re.sub(r"[\n\r]+", "\n", "\n".join(lines))


def format_repeater(repeater):
    downlink = ["%.5f MHz" % (repeater.frequency / 1000000)]
    if not _is_null_or_whitesace(repeater.decode):
        downlink.append("tone: " + repeater.decode.strip())

    uplink = ["%.5f MHz" % ((repeater.frequency + repeater.offset) / 1000000)]
    if not _is_null_or_whitesace(repeater.encode):
        uplink.append("tone: " + repeater.encode.strip())

    offset = "%0.3f MHz" % (repeater.offset / 1000000)

    res = f"""## {repeater.callsign}
{repeater.city}
"""
    if repeater.distance is not None:
        res += "Distance: %0.3f km\n" % repeater.distance

    res += f"""Mode: {repeater.mode}
Downlink: {", ".join(downlink)}
Uplink: {", ".join(uplink)}
Offset: {offset}
"""

    if not _is_null_or_whitesace(repeater.description):
        res += "\n" + _normalize_spaces(repeater.description)

    return res


def search_repeaters_by_location(lat, lon, max_distance=80, modes=None, bands=None):
    # Nothing to do if we don't have a database
    if not os.path.isfile(REPEATER_DATABASE):
        return None

    # If bands were provided, flatten them
    def _flatten_bands(b, lst):
        if isinstance(b, list):
            for elm in b:
                _flatten_bands(elm, lst)
        else:
            return lst.append(b)

    _bands = None
    if bands is not None:
        _bands = []
        _flatten_bands(bands, _bands)

    # If we were given a single mode, then put it in a list
    if isinstance(modes, str):
        modes = [modes]

    # Give us a "box" we can query with
    origin = (lat, lon)

    north = inverse_haversine(
        origin, max_distance, Direction.NORTH, unit=Unit.KILOMETERS
    )[0]
    south = inverse_haversine(
        origin, max_distance, Direction.SOUTH, unit=Unit.KILOMETERS
    )[0]
    east = inverse_haversine(
        origin, max_distance, Direction.EAST, unit=Unit.KILOMETERS
    )[1]
    west = inverse_haversine(
        origin, max_distance, Direction.WEST, unit=Unit.KILOMETERS
    )[1]

    # If we've gone all the way around, things get messy. Just open it up to everything.
    if south > north:
        north = 90
        south = -90
    if west > east:
        west = -180
        east = 180

    # Connect to the SQLite database
    conn = sqlite3.connect(REPEATER_DATABASE)
    cursor = conn.cursor()

    # SQL query to select a short-list of candidates
    cursor.execute(
        """SELECT
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
FROM Repeaters
WHERE 
    (latitude BETWEEN ? AND ?) AND
    (longitude BETWEEN ? AND ?);""",
        (south, north, west, east),
    )

    # Do the search
    results = []
    rows = cursor.fetchall()
    for row in rows:
        record = Repeater(
            id=row[0],
            callsign=row[1],
            latitude=row[2],
            longitude=row[3],
            city=row[4],
            category=row[5],
            internet_node=row[6],
            mode=row[7],
            encode=row[8],
            decode=row[9],
            frequency=row[10],
            offset=row[11],
            description=row[12],
            power=row[13],
            operational=row[14],
            restriction=row[15],
            distance=haversine(origin, (row[2], row[3]), unit=Unit.KILOMETERS),
        )

        # Check the distance
        if record.distance > max_distance:
            continue

        # Check the mode
        if modes is not None:
            found = False
            for mode in modes:
                if re.search(mode, record.mode):
                    found = True
                    break
            if found == False:
                continue

        # Check the band
        if _bands is not None:
            found = False
            for band in _bands:
                lf = band[0] * 1000000.0
                hf = band[1] * 1000000.0
                if lf <= record.frequency and record.frequency <= hf:
                    found = True
                    break
            if found == False:
                continue

        results.append(record)

    conn.close()

    # Sort the results by distance
    results.sort(key=lambda x: x.distance)
    return results


def search_repeaters_by_callsign(callsign, lat=None, lon=None, modes=None, bands=None):
    # Nothing to do if we don't have a database
    if not os.path.isfile(REPEATER_DATABASE):
        return None

    # If bands were provided, flatten them
    def _flatten_bands(b, lst):
        if isinstance(b, list):
            for elm in b:
                _flatten_bands(elm, lst)
        else:
            return lst.append(b)

    _bands = None
    if bands is not None:
        _bands = []
        _flatten_bands(bands, _bands)

    # If we were given a single mode, then put it in a list
    if isinstance(modes, str):
        modes = [modes]

    # Compute the origin for sorting on distance
    origin = None
    if lat is not None and lon is not None:
        origin = (lat, lon)

    # Connect to the SQLite database
    conn = sqlite3.connect(REPEATER_DATABASE)
    cursor = conn.cursor()

    # SQL query to select a short-list of candidates
    cursor.execute(
        """SELECT
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
FROM Repeaters
WHERE 
    callsign LIKE ? || '%';""",
        (callsign,),
    )

    # Do the search
    results = []
    rows = cursor.fetchall()
    for row in rows:
        record = Repeater(
            id=row[0],
            callsign=row[1],
            latitude=row[2],
            longitude=row[3],
            city=row[4],
            category=row[5],
            internet_node=row[6],
            mode=row[7],
            encode=row[8],
            decode=row[9],
            frequency=row[10],
            offset=row[11],
            description=row[12],
            power=row[13],
            operational=row[14],
            restriction=row[15],
            distance=None
            if origin is None
            else haversine(origin, (row[2], row[3]), unit=Unit.KILOMETERS),
        )

        # Check the mode
        if modes is not None:
            found = False
            for mode in modes:
                if re.search(mode, record.mode):
                    found = True
                    break
            if found == False:
                continue

        # Check the band
        if _bands is not None:
            found = False
            for band in _bands:
                lf = band[0] * 1000000.0
                hf = band[1] * 1000000.0
                if lf <= record.frequency and record.frequency <= hf:
                    found = True
                    break
            if found == False:
                continue

        results.append(record)

    conn.close()

    # Sort the results by distance
    if origin is not None:
        results.sort(key=lambda x: x.distance)

    return results
