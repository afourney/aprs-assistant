# SPDX-FileCopyrightText: 2024-present Adam Fourney <adam.fourney@gmail.com>
#
# SPDX-License-Identifier: MIT
import requests
import json
import os
import xmltodict

from ._cache import read_cache, write_cache
from ._constants import SECONDS_IN_MINUTE


def get_band_conditions():
    solar_json = xmltodict.parse(get_solarxml())["solar"]["solardata"]

    result = "# Solar-Terrestrial Data\n"
    result += "========================\n"
    for k in solar_json:
        if k not in ["source", "calculatedconditions", "calculatedvhfconditions"]:
            val = solar_json[k]
            if val is None:
                continue
            if isinstance(val, str):
                val = val.strip()
            result += f"{k}: {val}\n"

    result = result.strip()
    result += "\n\n# HF Conditions\n"
    result += "===============\n"

    for b in solar_json["calculatedconditions"]["band"]:
        result += b["@name"] + " " + b["@time"] + " " + b["#text"] + "\n"

    result = result.strip()
    result += "\n\n# VHF Phenomenon\n"
    result += "================\n"
    for b in solar_json["calculatedvhfconditions"]["phenomenon"]:
        result += b["@location"] + " " + b["@name"] + ": " + b["#text"] + "\n"

    return result


def get_solarxml():
    cache_key = f"get_band_conditions"
    cached_data = read_cache(cache_key)
    if cached_data is not None:
        return cached_data
    else:
        data = _get_solarxml()
        write_cache(cache_key, data, expires_in=SECONDS_IN_MINUTE * 30)
        return data


def _get_solarxml():
    headers = {"User-Agent": "aprsd_gpt_plugin"}
    response = requests.get(
        f"https://www.hamqsl.com/solarxml.php", headers=headers, stream=False
    )
    response.raise_for_status()
    return response.text
