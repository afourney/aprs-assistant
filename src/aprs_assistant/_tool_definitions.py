TOOL_WEB_SEARCH = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": "Perform a Bing web search. Useful when answering most user questions.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The web search query to use.",
                },
            },
            "required": ["query"],
        },
    },
}

TOOL_USER_WEATHER = {
    "type": "function",
    "function": {
        "name": "user_weather",
        "description": "Look up the current weather conditions and 3-day forecast at the user's current (or last-known) location.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
}

TOOL_REGIONAL_WEATHER = {
    "type": "function",
    "function": {
        "name": "regional_weather",
        "description": "Look up the current weather conditions and 3-day forecast at a regional postal code or city level. This is less accurate than user_weather. Use user_weather when the user's precise location is known.",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "The city or town to look up.",
                },
                "state": {
                    "type": "string",
                    "description": "The state or province.",
                },
                "country": {
                    "type": "string",
                    "description": "The country.",
                },
                "postalcode": {
                    "type": "string",
                    "description": "The zipcode or potal code.",
                },
            },
            "required": [],
        },
    },
}

TOOL_BAND_CONDITIONS = {
    "type": "function",
    "function": {
        "name": "radio_band_conditions",
        "description": "Lookup the latest HF and VHF band conditions, as well as other solar and space weather conditions that may impact radio operations.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
}

TOOL_CALLSIGN_SEARCH = {
    "type": "function",
    "function": {
        "name": "callsign_search",
        "description": "Perform a lookup on a radio operator's call sign.",
        "parameters": {
            "type": "object",
            "properties": {
                "callsign": {
                    "type": "string",
                    "description": "The call sign to search.",
                },
            },
            "required": ["callsign"],
        },
    },
}
