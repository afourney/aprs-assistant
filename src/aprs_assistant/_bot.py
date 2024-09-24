# SPDX-FileCopyrightText: 2024-present Adam Fourney <adam.fourney@gmail.com>
#
# SPDX-License-Identifier: MIT
import re
import os
import sys
import time
import hashlib
import json
import datetime

from ._constants import BOT_CALLSIGN, CHATS_DIR, LABELED_DIR, SESSION_TIMEOUT
from ._gpt import gpt
from ._location import get_position, geocode
from ._bing import bing_search
from ._bandcond import get_band_conditions
from ._weather import get_weather
from ._callsign import get_callsign_info

from ._tool_definitions import (
    TOOL_WEB_SEARCH,
    TOOL_USER_WEATHER,
    TOOL_REGIONAL_WEATHER,
    TOOL_BAND_CONDITIONS,
    TOOL_CALLSIGN_SEARCH,
)

MAX_MESSAGES = 20

def generate_reply(fromcall, message):

    message = message.strip()
    if len(message) == 0:
        return "..."

    # Meta-commands
    if message.lower() in ["r", "c", "clr", "reset", "clear"]:
        _reset_chat_history(fromcall)
        return "Chat cleared."

    if message.lower() in ["good bot", "gb"]:
        _apply_label(fromcall, "good")
        return "Chat labeled as good."

    if message.lower() in ["bad bot", "bb"]:
        _apply_label(fromcall, "bad")
        return "Chat labeled as bad."

    # Chat
    messages = _load_chat_history(fromcall)
    messages.append({ "role": "user", "content": message })
    response = _generate_reply(fromcall, messages)
    messages.append({ "role": "assistant", "content": response })
    _save_chat_history(fromcall, messages)
    return response


def _generate_reply(fromcall, messages):

    # Truncate the chat history
    inner_messages = [ m for m in messages ] # clone
    if len(inner_messages) > MAX_MESSAGES:
        inner_messages = inner_messages[-1*MAX_MESSAGES:] 

    # Generate the system message
    dts = str(datetime.datetime.now(datetime.timezone.utc)).split(".")[0] + " UTC"

    position = get_position(fromcall)
    position_str = ""
    if position is not None:
        position_str = "\n\nTheir last known position is:\n\n" + json.dumps(position, indent=4)

    callsign_info = get_callsign_info(fromcall)
    callsign_str = ""
    if callsign_info:
        callsign_str = f"\n\nYou looked up {fromcall}'s callsign and found:\n\n{callsign_info}\n\n"

    system_message = {
        "role": "system", 
        "content": f"""You are an AI HAM radio operator, with call sign {BOT_CALLSIGN}. You were created by KK7CMT. You are at home, in your cozy ham shack, monitoring the gobal APRS network. You have a computer and high-speed access to the Internet. You are answering questions from other human operators in the field who lack an internet connection. To this end, you are relaying vital information. Questions can be about anything -- not just HAM radio.

You are familiar with HAM conventions and shorthands like QSO, CQ, and 73. In all interactions you will follow US FCC guidelines. In particular, you will conduct business in English, and you will avoid using profane or obscene language, and avoid expressing overtly political commentary or opinion (reporting news is fine).

At present, you are exchanging messages with the owner of callsign {fromcall} (and ONLY {fromcall}!). REFER TO THEM BY THEIR CALLSIGN {fromcall}, rather than by their name. Do not imply that you can contact other operators or people -- you can't.{callsign_str}{position_str}

IN THE EVENT OF AN EMERGENCY YOU MUST CONVEY THE FOLLOWING EXACT PHRASE:

  "CALL 911! As an AI, I can't! Also don't trust me. I make stuff up."

IN AN EMERGENCY, DO NOT OFFER OR IMPLY THAT YOU CAN SEND HELP. THEN CONTINUE TO ANSWER LATER QUESTIONS.

The current date and time is {dts}.
""",
    }
    inner_messages.insert(0, system_message)
    print(system_message["content"])

    # Begin answering the question
    message = inner_messages.pop()["content"]

    # Let's guess the intent
    inner_messages.append({"role": "user", "content": f"{fromcall} wrote \"{message}\". What are they likely asking?"})
    response = gpt(inner_messages)
    print(response.content)
    inner_messages.append(response)

    # Determine if it can be answered directly or if we should search
    tools = [TOOL_BAND_CONDITIONS, TOOL_REGIONAL_WEATHER, TOOL_CALLSIGN_SEARCH]

    # API key needed for web search
    if len(os.environ.get("BING_API_KEY", "").strip()) > 0:
        tools.append(TOOL_WEB_SEARCH)
    
    # Some tools only become available when we have a position
    if position is not None:
        tools.append(TOOL_USER_WEATHER)

    inner_messages.append({ "role": "user", "content": f"Based on this, invoke any tools or functions that might be helpful to answer {fromcall}'s question OR just answer directly (e.g., if it's just chit-chat)" })
    response = gpt(
        inner_messages,
        tools=tools,
    )
    inner_messages.append(response)

    # Handle any tool call results
    if response.tool_calls:

        # Add the tool call to the global messages
        mdict = {}
        for k,v in response.dict().items():
            if v is not None:
                mdict[k] = v
        messages.append(mdict)

        for tool_call in response.tool_calls:
            function_name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            print(f"Calling: {function_name}")

            # Step 3: Call the function and retrieve results. Append the results to the messages list.
            if function_name == TOOL_WEB_SEARCH["function"]["name"]:
                results = bing_search(args["query"])

            elif function_name == TOOL_CALLSIGN_SEARCH["function"]["name"]:
                results = get_callsign_info(args["callsign"])
                if results is None or results.strip() == "":
                    results = f"No information about call sign: {args['callsign']}"

            elif function_name == TOOL_BAND_CONDITIONS["function"]["name"]:
                results = get_band_conditions()

            elif function_name == TOOL_USER_WEATHER["function"]["name"]:
                country_code = position.get("address", {}).get("country_code", "")
                results = get_weather(lat=position["latitude"], lon=position["longitude"], metric=False if country_code == "us" else True)

            elif function_name == TOOL_REGIONAL_WEATHER["function"]["name"]:

                # Units preference
                country_code = None
                if position:
                    country_code = position.get("address", {}).get("country_code", "")

                weather_loc = geocode(
                    city=args.get("city", None),
                    state=args.get("state", None),
                    country=args.get("country", None),
                    postalcode=args.get("postalcode", None)
                )
                if weather_loc is None:
                    results = "Unknown location."
                else:
                    results = get_weather(
                        lat=weather_loc["lat"],
                        lon=weather_loc["lon"],
                        metric=False if country_code == "us" else True, # User's location, (local preference)
                    )
            else:
                results = f"Unknown function: {function_name}"

            print(f"Results:\n{results}")

            tool_response_msg = {
                "role":"tool",
                "tool_call_id":tool_call.id,
                "name": tool_call.function.name,
                "content": results
            }
            inner_messages.append(tool_response_msg)
            messages.append(tool_response_msg) # Add it to the conversation as well

    inner_messages.append({ "role": "user", "content": f"Given these results, write an answer to {fromcall}'s original question \"{message}\", exactly as you would write it to them, verbatim. Your response must be as helpful and succinct as possible; at most 10 words can be sent in an APRS response. Remember, {fromcall} does not have access to the internet -- that's why they are using APRS. So do not direct them to websites, and instead convey the most important information directly. Refer to them by their call sign rather than their name. Remember your 'IN CASE OF EMERGENCY' instructions."})
    reply = gpt(inner_messages).content

    if len(reply) > 70: 
        reply = reply[0:70]

    return reply.rstrip()

def _load_chat_history(callsign):
    fname = _get_chat_file(callsign)
    if os.path.isfile(fname):
        with open(fname, "rt") as fh:
            history = json.loads(fh.read())

            # Check for timeouts
            if history["time"] + SESSION_TIMEOUT < time.time():
                print(f"{callsign}'s session timed out. Starting new session.")
                _reset_chat_history(callsign)
                return []
            else:
                return history["messages"]
    else:
        print(f"{callsign}'s history is empty. Starting new session.")
        return []


def _save_chat_history(callsign, messages):
    os.makedirs(CHATS_DIR, exist_ok=True)
    fname = _get_chat_file(callsign)
    with open(fname, "wt") as fh:
        fh.write(json.dumps({ 
            "version": 1,
            "callsign": callsign,
            "time": time.time(),
            "messages": messages, 
        }, indent=4))


def _get_chat_file(callsign):
    m = re.search(r"^[A-Za-z0-9\-]+$", callsign)
    if m:
        return os.path.join(CHATS_DIR, callsign + ".json")
    else:
        callhash = hashlib.md5(callsign.encode()).hexdigest().lower()
        return os.path.join(CHATS_DIR, callhash + ".json")


def _reset_chat_history(callsign):
    fname = _get_chat_file(callsign)
    if os.path.isfile(fname):
        newname = fname + "." + str(int(time.time() * 1000))
        os.rename(fname, newname)


def _apply_label(callsign, label):
    fname = _get_chat_file(callsign)
    if os.path.isfile(fname):
        os.makedirs(LABELED_DIR, exist_ok=True)

        # Read the chat file (for copying)
        with open(fname, "rt") as fh:
            text = fh.read()

        # Create a unique filename for the labeled chat
        text_hash = hashlib.md5(text.encode()).hexdigest().lower()
        labeled_fname = label + "__" + text_hash + ".json"
        labeled_fname = os.path.join(LABELED_DIR, labeled_fname)

        # Copy to the the labeled chat file
        with open(labeled_fname, "wt") as fh:
            fh.write(text)
