# SPDX-FileCopyrightText: 2024-present Adam Fourney <adam.fourney@gmail.com>
#
# SPDX-License-Identifier: MIT
import os
import json
from openai import AzureOpenAI, OpenAI

# from azure.identity import DefaultAzureCredential, get_bearer_token_provider

_oai_client = None


def gpt(messages, model="gpt-4o-2024-08-06", json_mode=False, **kwargs):
    global _oai_client

    if _oai_client is None:
        _oai_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    kwargs["model"] = model
    kwargs["messages"] = messages

    if json_mode == False:
        response = _oai_client.chat.completions.create(**kwargs)
        return response.choices[0].message
    else:
        kwargs["response_format"] = {"type": "json_object"}
        response = _oai_client.chat.completions.create(**kwargs)
        return json.loads(response.choices[0].message)
