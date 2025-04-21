import os
from dotenv import load_dotenv
from serpapi import GoogleSearch
import requests
import re
from duckduckgo_search import DDGS


load_dotenv()


def search_serp(url_to_check: str) -> list[str]:
    # Search Google for the URL
    query = f'intext:{url_to_check} -site:{url_to_check}'
    search_params = {
        "q": query,  # Search for the event name
        "api_key": os.getenv("SERP_API_KEY"),
        "num": 10,  # Number of results to return
        "no_cache": True,
    }

    # Perform the search using SerpAPI
    serp_search = GoogleSearch(search_params)
    data = serp_search.get_dict()
    if "error" in data:
        print(f"Error: {data['error']}")
        return []
    if "organic_results" not in data:
        print("No organic results found.")
        return []
    return [res.get("link") for res in data.get("organic_results", [])]


def search_serper(url_to_check: str) -> list[str]:
    # Search Google for the URL
    query = f'\\"{url_to_check}\\" -site:{url_to_check}'
    search_params = {
        "q": query,  # Search for the event name
        "api_key": os.getenv("SERPER_API_KEY"),
    }

    # Perform the search using SerperAPI
    base_url = "https://google.serper.dev/search"
    response = requests.get(base_url, params=search_params)
    data = response.json()
    if response.status_code != 200:
        print(f"Error: {data.get('message', 'Unknown error')}")
        return []
    if 'Query not allowed.' in data.get('message', []):
        return []
    return [res.get("link") for res in data.get("organic", [])]


def search_ddg(query):
    url = "https://api.duckduckgo.com/"
    params = {"q": query, "format": "json"}
    response = requests.get(url, params=params)
    return response.json()


def ddgs_search(url_to_check):
    """Perform a DuckDuckGo search for the given query."""
    ddgs = DDGS(
        headers={
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
    )
    results = []
    query = f"'{url_to_check}' -site:{url_to_check}"
    for result in ddgs.text(query, max_results=5, backend="html"):
        results.append(result.get("href"))
    return results

def query_serp(query):
    search_params = {
        "q": query,
        "api_key": os.getenv("SERP_API_KEY"),
        "engine": "google",
        "google_domain": "google.com",
    }
    base_url = "https://serpapi.com/search.json"
    response = requests.get(base_url, params=search_params)

    if response.status_code == 200:
        results = response.json()
    else:
        raise ValueError(response.json())
    return results

def query_serper(query: str) -> dict[str]:
    search_params = {
        "q": query,  # Search for the event name
        "api_key": os.getenv("SERPER_API_KEY"),
        "num": 10,  # Number of results to return
    }

    # Perform the search using SerperAPI
    base_url = "https://google.serper.dev/search"
    response = requests.get(base_url, params=search_params)
    if response.status_code == 200:
        results = response.json()
    else:
        raise ValueError(response.json())
    return results

