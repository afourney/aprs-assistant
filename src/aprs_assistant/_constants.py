# SPDX-FileCopyrightText: 2024-present Adam Fourney <adam.fourney@gmail.com>
#
# SPDX-License-Identifier: MIT
import os
from .__about__ import __version__

BOT_CALLSIGN = os.environ.get("APRS_ASSISTANT_CALLSIGN", "<NOCALL>")

DATA_DIR = os.path.join(os.getcwd(), "data")
CACHE_DIR = os.path.join(DATA_DIR, "cache")
CHATS_DIR = os.path.join(DATA_DIR, "chats")
LABELED_DIR = os.path.join(DATA_DIR, "labeled")
FCC_DATABASE = os.path.join(DATA_DIR, "fcc_uls.db")

USER_AGENT = "aprs-assistant/" + __version__

# Number of seconds (for cacheing etc.)
SECONDS_IN_MINUTE = 60
SECONDS_IN_HOUR = SECONDS_IN_MINUTE * 60
SECONDS_IN_DAY = SECONDS_IN_HOUR * 24
SECONDS_IN_WEEK = SECONDS_IN_DAY * 7

SESSION_TIMEOUT = 30 * SECONDS_IN_MINUTE
