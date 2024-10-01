# APRS Assistant

[![PyPI - Version](https://img.shields.io/pypi/v/aprs-assistant.svg)](https://pypi.org/project/aprs-assistant)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/aprs-assistant.svg)](https://pypi.org/project/aprs-assistant)

An LLM-based assistant for the Automatic Packet Reporting System (APRS).

> [!IMPORTANT]
> This library provides core functionality for an LLM-based APRS chatbot, but does not itself directly handle APRS messaging (RX, or TX). **If you want to run APRS Assistant yourself, on the APRS IS network, you should visit the sister project [aprs-assistant-plugin](https://github.com/afourney/aprsd-assistant-plugin), which has everything you need.**

For local development, or to integrate APRS Assistant into other frameworks, read on. For running APRS Assistant, heed the above advice and go to [aprs-assistant-plugin](https://github.com/afourney/aprsd-assistant-plugin) now.

---

## Installation

```console
pip install aprs-assistant
```

## Callsign

Your bot needs a callsign! Set with the `APRS_ASSISTANT_CALLSIGN` environment variable.

```console
export APRS_ASSISTANT_CALLSIGN=<CLEVER_CALLSIGN>
```

## API Keys

At a minimum, this library requires setting an OpenAI API key. Bing and APRS.fi API keys are also used to support various tools and services. Set the, as environment variable in bash, as follows:

```console
export OPENAI_API_KEY=<YOUR_KEY>
export BING_API_KEY=<YOUR_KEY>
export APRSFI_API_KEY=<YOUR_KEY>
```

## Running Local Chat

The library supports local chats (e.g., for debugging) as follows:

```console
python -m aprs_assistant <YOUR_CALLSIGN>
```

Type `exit` or press `Ctrl-D` to exit.

## FCC ULS Integration

APRS Assistant supports basic callsign lookups using a local copy of the FCC ULS database. This database is about 325 MB and is easily created.

```
cd ./tools/parse_fcc_uls
bash create_db.bash
cd ../..
mkdir data
mv ./tools/parse_fcc_uls/fcc_uls.db data/.
```

This step only needs to be done once (or when you wish to update the database with new records!)

See `./tools/parse_fcc_uls/README` for more details.

## Integration

To integrate `aprs-assistant` into your application, simply use:

```
from aprs_assistant import generate_reply

sender_callsign = "NOCALL"
message = "What's the weather?"
response = generate_reply(sender_callsign, message)

print(response)
```

Note: `response` can be None

## License

`aprs-assistant` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
