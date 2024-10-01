# SPDX-FileCopyrightText: 2024-present Adam Fourney <adam.fourney@gmail.com>
#
# SPDX-License-Identifier: MIT
import sys
import os
import json
from ._bot import generate_reply
from ._constants import BOT_CALLSIGN, FCC_DATABASE

if os.environ.get("OPENAI_API_KEY", "").strip() == "":
    raise ValueError(
        "No OPENAI_API_KEY. Please set the OPENAI_API_KEY environment variable."
    )

if os.environ.get("BING_API_KEY", "").strip() == "":
    sys.stderr.write(
        "Warning: No BING_API_KEY. Web searches are disabled.\nPlease set the BING_API_KEY environment variable.\n\n"
    )

if os.environ.get("APRSFI_API_KEY", "").strip() == "":
    sys.stderr.write(
        "Warning: No APRSFI_API_KEY. Location lookups, and localized features (e.g., local weather) are disabled.\nPlease set the APRSFI_API_KEY environment variable.\n\n"
    )

if not os.path.isfile(FCC_DATABASE):
    sys.stderr.write(
        f"Warning: FCC Database not found at '{FCC_DATABASE}'.\nThis is easily fixed!\nSee './tools/parse_fcc_uls/README.md'\n\n"
    )

if len(sys.argv) < 2:
    sys.stderr.write("SYNTAX: python -m aprs-assistant <YOUR_CALLSIGN>\n\n")
    sys.exit(0)

fromcall = sys.argv[1]
while True:
    request = input(f"{fromcall}: ").strip()
    if len(request) == 0:
        continue
    if request == "quit" or request == "exit":
        break
    response = generate_reply(fromcall, request)
    print(f"\n{BOT_CALLSIGN}: {response}\n")
