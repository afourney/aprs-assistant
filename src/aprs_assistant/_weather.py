# SPDX-FileCopyrightText: 2024-present Adam Fourney <adam.fourney@gmail.com>
#
# SPDX-License-Identifier: MIT
import requests
import json
import os
import xmltodict
import re

from ._cache import read_cache, write_cache
from ._constants import SECONDS_IN_MINUTE, USER_AGENT

# built with: https://open-meteo.com/en/docs
OPEN_METEO_URL="https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=weather_code,temperature_2m,relative_humidity_2m,apparent_temperature,is_day,precipitation,rain,showers,snowfall,cloud_cover,pressure_msl,surface_pressure,wind_speed_10m,wind_direction_10m,wind_gusts_10m&minutely_15=precipitation,rain,snowfall,weather_code,wind_speed_10m,wind_direction_80m,wind_gusts_10m&hourly=temperature_2m,relative_humidity_2m,dew_point_2m,apparent_temperature,precipitation_probability,precipitation,rain,showers,snowfall,snow_depth,weather_code,pressure_msl,surface_pressure,cloud_cover,cloud_cover_low,cloud_cover_mid,cloud_cover_high,visibility,wind_speed_10m,wind_direction_10m,wind_gusts_10m,uv_index&daily=weather_code,temperature_2m_max,temperature_2m_min,apparent_temperature_max,apparent_temperature_min,sunrise,sunset,uv_index_max,uv_index_clear_sky_max,precipitation_sum,rain_sum,showers_sum,snowfall_sum,precipitation_hours,precipitation_probability_max,wind_speed_10m_max,wind_gusts_10m_max,wind_direction_10m_dominant&timezone={timezone}&forecast_days=3&forecast_hours=24&forecast_minutely_15=24"
OPEN_METEO_IMPERIAL_PARAMS="&temperature_unit=fahrenheit&wind_speed_unit=mph&precipitation_unit=inch"

WEATHER_CODES = {
    0: "Sunny",
    1: "Mainly Sunny",
    2: "Partly Cloudy",
    3: "Cloudy",
    45: "Foggy",
    48: "Rime Fog",
    51: "Light Drizzle",
    53: "Drizzle",
    55: "Heavy Drizzle",
    56: "Light Freezing Drizzle",
    57: "Freezing Drizzle",
    61: "Light Rain",
    63: "Rain",
    65: "Heavy Rain",
    66: "Light Freezing Rain",
    67: "Freezing Rain",
    71: "Light Snow",
    73: "Snow",
    75: "Heavy Snow",
    77: "Snow Grains",
    80: "Light Showers",
    81: "Showers",
    82: "Heavy Showers",
    85: "Light Snow Showers",
    86: "Snow Showers",
    95: "Thunderstorm",
    96: "Light Thunderstorms With Hail",
    99: "Thunderstorm With Hail"
}

def get_weather(lat, lon, metric=True):
    meteo_data = get_open_meteo_weather(lat, lon, metric=metric)

    result = ""

    # Bulletins
    bulletins = format_noaa_alerts(_get_noaa_alerts(lat, lon), abbreviated=True)
    if bulletins is not None and bulletins.strip() != "":
        result += "# Bulletins\n===========\n" + bulletins.strip() + "\n\n"

    # Current conditions
    current_cond_time = re.sub("T", " ", meteo_data["current"]["time"]) + " " + meteo_data["timezone_abbreviation"] 

    current_title = f"# Current Conditions (as of {current_cond_time})"
    result += current_title + "\n" + ("="*len(current_title)) + "\n"
    for k in meteo_data["current"]:
        if k in ["time", "interval", "is_day"]:
            continue

        val = meteo_data["current"][k]
        unit = meteo_data["current_units"][k]
        
        if unit == "wmo code":
            if val in WEATHER_CODES:
                unit = ""
                val = WEATHER_CODES[val]
                k = "weather"
            else:
                continue

        k = re.sub("_", " ", k).title() # Convert to human label
        k = re.sub(r" \d+M\b", "", k) # Remove elevation 
        result += f"* {k}: {val} {unit}\n"

    # 3-day forcast
    result += f"\n# 3-day Forecast"
    result += f"\n================\n"

    def _format_daily(idx):
        res = ""
        for k in meteo_data["daily"]:
            if k in ["time"]:
                continue
            val = meteo_data["daily"][k][idx]
            unit = meteo_data["daily_units"][k]

            if unit == "iso8601":
                val = val.split("T")[-1] # Keep only the time
                unit = meteo_data["timezone_abbreviation"]

            if unit == "wmo code":
                if val in WEATHER_CODES:
                    unit = ""
                    val = WEATHER_CODES[val]
                    k = "weather"
                else:
                    continue

            k = re.sub("_", " ", k).title() # Convert to human label
            k = re.sub(r" \d+M\b", "", k) # Remove elevation 
            res += f"* {k}: {val} {unit}\n"
        return res

    result += "### Today\n" + _format_daily(0) + "\n"
    result += "### Tomorrow\n" + _format_daily(1) + "\n"
    result += "### " + meteo_data["daily"]["time"][2] + "\n" + _format_daily(1) + "\n"

    return result.strip()


def get_open_meteo_weather(lat, lon, metric=True):
    cache_key = f"get_open_meteo_weather:{lat}:{lon}:{metric}"
    cached_data = read_cache(cache_key)
    if cached_data is not None:
        return cached_data
    else:
        data = _get_open_meteo_weather(lat, lon, metric=metric)
        write_cache(cache_key, data, expires_in=SECONDS_IN_MINUTE*30)
        return data


def _get_open_meteo_weather(lat, lon, metric=True):
    headers = { "User-Agent": USER_AGENT }
    response = requests.get(
        OPEN_METEO_URL.format( lat=lat, lon=lon, timezone="auto" ) + ("" if metric else OPEN_METEO_IMPERIAL_PARAMS),
        headers=headers,
        stream=False
    )
    response.raise_for_status()
    return response.json()


def get_noaa_alerts(lat, lon):
    cache_key = f"get_noaa_alerts:{lat}:{lon}"
    cached_data = read_cache(cache_key)
    if cached_data is not None:
        return cached_data
    else:
        data = _get_noaa_alerts(lat, lon)
        write_cache(cache_key, data, expires_in=SECONDS_IN_MINUTE*5)
        return data


def _get_noaa_alerts(lat, lon):
    # Documentation: https://www.weather.gov/documentation/services-web-api#/default/alerts_active
    headers = { 
        "Accept": "application/ld+json",
        "User-Agent": USER_AGENT 
    }
    response = requests.get(
        f"https://api.weather.gov/alerts/active?point={lat},{lon}",
        headers=headers,
        stream=False
    )
    response.raise_for_status()
    return response.json()


def format_noaa_alerts( alerts, abbreviated=False ):
    results = []
    for a in alerts.get("@graph", []):
        fa = format_noaa_alert( a, abbreviated=abbreviated )
        if fa is not None:
            fa = fa.strip()
            if fa != "":
                results.append(fa)

    return "\n\n".join(results)


def format_noaa_alert( alert, abbreviated=False ):
    abbreviated=True
    if abbreviated:
        parameters = alert.get("parameters", None)
        if parameters is None:
            return None
        headlines = parameters.get("NWSheadline", [])
        if len(headlines) == 0:
            headlines = [ alert.get("headline", "") ]
        headlines = "\n".join( [f"**{h}**" for h in headlines] ) 

        instruction = alert.get("instruction", None)
        if instruction is None or instruction.strip() == "":
            instruction = alert.get("response", "")
        instruction = re.sub(r"\s+", " ", instruction).strip()

        flags = []
        for f in [ alert.get("severity", None), alert.get("urgency", None), alert.get("certainty", None), ]:
            if f is not None and f.strip() not in ["", "Unknown", "Past"]:
                flags.append(f.strip())
        flags = " / ".join(flags)

        return f"{headlines}\n{flags}\nInstruction: {instruction}"
    else:
        result = ""


