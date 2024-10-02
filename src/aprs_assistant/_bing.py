# SPDX-FileCopyrightText: 2024-present Adam Fourney <adam.fourney@gmail.com>
#
# SPDX-License-Identifier: MIT
#
# Adapted from:
#   AutoGen (Copyright 2024, Microsoft Corporation; MIT Licensed)
#   https://github.com/microsoft/autogen/blob/headless_web_surfer/autogen/browser_utils/markdown_search.py

import json
import requests
import re
import os
from urllib.parse import quote, quote_plus, unquote, urlparse, urlunparse


# from: https://learn.microsoft.com/en-us/bing/search-apis/bing-web-search/reference/market-codes
BING_MARKETS = [
    ("Argentina", "Spanish", "es-AR"),
    ("Australia", "English", "en-AU"),
    ("Austria", "German", "de-AT"),
    ("Belgium", "Dutch", "nl-BE"),
    ("Belgium", "French", "fr-BE"),
    ("Brazil", "Portuguese", "pt-BR"),
    ("Canada", "English", "en-CA"),
    ("Canada", "French", "fr-CA"),
    ("Chile", "Spanish", "es-CL"),
    ("Denmark", "Danish", "da-DK"),
    ("Finland", "Finnish", "fi-FI"),
    ("France", "French", "fr-FR"),
    ("Germany", "German", "de-DE"),
    ("Hong Kong SAR", "Traditional Chinese", "zh-HK"),
    ("India", "English", "en-IN"),
    ("Indonesia", "English", "en-ID"),
    ("Italy", "Italian", "it-IT"),
    ("Japan", "Japanese", "ja-JP"),
    ("Korea", "Korean", "ko-KR"),
    ("Malaysia", "English", "en-MY"),
    ("Mexico", "Spanish", "es-MX"),
    ("Netherlands", "Dutch", "nl-NL"),
    ("New Zealand", "English", "en-NZ"),
    ("Norway", "Norwegian", "no-NO"),
    ("People's republic of China", "Chinese", "zh-CN"),
    ("Poland", "Polish", "pl-PL"),
    ("Republic of the Philippines", "English", "en-PH"),
    ("Russia", "Russian", "ru-RU"),
    ("South Africa", "English", "en-ZA"),
    ("Spain", "Spanish", "es-ES"),
    ("Sweden", "Swedish", "sv-SE"),
    ("Switzerland", "French", "fr-CH"),
    ("Switzerland", "German", "de-CH"),
    ("Taiwan", "Traditional Chinese", "zh-TW"),
    ("Turkey", "Turkish", "tr-TR"),
    ("United Kingdom", "English", "en-GB"),
    ("United States", "English", "en-US"),
    ("United States", "Spanish", "es-US"),
]


def bing_search(query, lat=None, lon=None, interleave_results=True, market=None):
    results = _bing_api_call(query, lat, lon, market)
    snippets = {}

    def _processFacts(elm):
        facts = list()
        for e in elm:
            k = e["label"]["text"]
            v = " ".join(item["text"] for item in e["items"])
            facts.append(f"{k}: {v}")
        return "\n".join(facts)

    # Web pages
    # __POS__ is a placeholder for the final ranking position, added at the end
    web_snippets = list()
    if "webPages" in results:
        label = "[WEB] " if interleave_results else ""
        for page in results["webPages"]["value"]:
            snippet = f"__POS__. {label}{_markdown_link(page['name'], page['url'])}\n{page['snippet']}"

            if "richFacts" in page:
                snippet += "\n" + _processFacts(page["richFacts"])

            if "mentions" in page:
                snippet += "\nMentions: " + ", ".join(
                    e["name"] for e in page["mentions"]
                )

            if page["id"] not in snippets:
                snippets[page["id"]] = list()
            snippets[page["id"]].append(snippet)
            web_snippets.append(snippet)

            if "deepLinks" in page:
                for dl in page["deepLinks"]:
                    deep_snippet = f"__POS__. {label}{_markdown_link(dl['name'], dl['url'])}\n{dl['snippet'] if 'snippet' in dl else ''}"
                    snippets[page["id"]].append(deep_snippet)
                    web_snippets.append(deep_snippet)

    # News results
    news_snippets = list()
    if "news" in results:
        label = "[NEWS] " if interleave_results else ""
        for page in results["news"]["value"]:
            snippet = f"__POS__. {label}{_markdown_link(page['name'], page['url'])}\n{page.get('description', '')}".strip()

            if "datePublished" in page:
                snippet += "\nDate published: " + page["datePublished"].split("T")[0]

            if "richFacts" in page:
                snippet += "\n" + _processFacts(page["richFacts"])

            if "mentions" in page:
                snippet += "\nMentions: " + ", ".join(
                    e["name"] for e in page["mentions"]
                )

            news_snippets.append(snippet)

        if len(news_snippets) > 0:
            snippets[results["news"]["id"]] = news_snippets

    # Videos
    video_snippets = list()
    if "videos" in results:
        label = "[VIDEO] " if interleave_results else ""
        for page in results["videos"]["value"]:
            if not page["contentUrl"].startswith("https://www.youtube.com/watch?v="):
                continue

            snippet = f"__POS__. {label}{_markdown_link(page['name'], page['contentUrl'])}\n{page.get('description', '')}".strip()

            if "datePublished" in page:
                snippet += "\nDate published: " + page["datePublished"].split("T")[0]

            if "richFacts" in page:
                snippet += "\n" + _processFacts(page["richFacts"])

            if "mentions" in page:
                snippet += "\nMentions: " + ", ".join(
                    e["name"] for e in page["mentions"]
                )

            video_snippets.append(snippet)

        if len(video_snippets) > 0:
            snippets[results["videos"]["id"]] = video_snippets

    # Related searches
    related_searches = ""
    if "relatedSearches" in results:
        related_searches = "## Related Searches:\n"
        for s in results["relatedSearches"]["value"]:
            related_searches += "- " + s["text"] + "\n"
        snippets[results["relatedSearches"]["id"]] = [related_searches.strip()]

    idx = 0
    content = ""
    if interleave_results:
        # Interleaved
        for item in results["rankingResponse"]["mainline"]["items"]:
            _id = item["value"]["id"]
            if _id in snippets:
                for s in snippets[_id]:
                    if "__POS__" in s:
                        idx += 1
                        content += s.replace("__POS__", str(idx)) + "\n\n"
                    else:
                        content += s + "\n\n"
    else:
        # Categorized
        if len(web_snippets) > 0:
            content += "## Web Results\n\n"
            for s in web_snippets:
                if "__POS__" in s:
                    idx += 1
                    content += s.replace("__POS__", str(idx)) + "\n\n"
                else:
                    content += s + "\n\n"
        if len(news_snippets) > 0:
            content += "## News Results\n\n"
            for s in news_snippets:
                if "__POS__" in s:
                    idx += 1
                    content += s.replace("__POS__", str(idx)) + "\n\n"
                else:
                    content += s + "\n\n"
        if len(video_snippets) > 0:
            content += "## Video Results\n\n"
            for s in video_snippets:
                if "__POS__" in s:
                    idx += 1
                    content += s.replace("__POS__", str(idx)) + "\n\n"
                else:
                    content += s + "\n\n"
        if len(related_searches) > 0:
            content += related_searches

    return f"## A Bing search for '{query}' found {idx} results:\n\n" + content.strip()


def _bing_api_call(query, lat=None, lon=None, market=None):
    # Resolve the market if it's just a country code
    if isinstance(market, str) and len(market) == 2:
        market = _get_market(market)

    # Prepare the request parameters
    request_kwargs = {}
    request_kwargs["headers"] = {}
    request_kwargs["headers"]["Ocp-Apim-Subscription-Key"] = os.environ["BING_API_KEY"]

    # Specify the user's location
    if lat is not None or lon is not None:
        if lat is None or lon is None:
            raise ValueError("If lat is specified, lon must also be specified.")
        request_kwargs["headers"]["X-Search-Location"] = f"lat:{lat};long:{lon};re:22m"

    request_kwargs["params"] = {}
    request_kwargs["params"]["q"] = query
    request_kwargs["params"]["textDecorations"] = False
    request_kwargs["params"]["textFormat"] = "raw"

    if market is not None:
        request_kwargs["params"]["mkt"] = market

    request_kwargs["stream"] = False

    # Make the request
    response = requests.get(
        "https://api.bing.microsoft.com/v7.0/search", **request_kwargs
    )
    response.raise_for_status()
    results = response.json()

    return results


def _markdown_link(anchor, href):
    try:
        parsed_url = urlparse(href)
        href = urlunparse(parsed_url._replace(path=quote(unquote(parsed_url.path))))
        anchor = re.sub(r"[\[\]]", " ", anchor)
        return f"[{anchor}]({href})"
    except ValueError:  # It's not clear if this ever gets thrown
        return f"[{anchor}]({href})"


def _get_market(country_code):
    country_code = country_code.upper()
    for market in BING_MARKETS:
        cc = market[2].split("-")[1]
        if cc.upper() == country_code:
            return market[2]
    return None
