import time

import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse
from duckduckgo_search import DDGS
from googlesearch import search
from smolagents import CodeAgent, tool, LiteLLMModel, DuckDuckGoSearchTool


@tool
def verify_event_website(event_name: str, url: str) -> dict:
    """
    Verifies the authenticity of a website for a given event by analyzing its content.

    This function checks various aspects of a webpage to determine if it's likely to be the official website for a specific event.
    It analyzes the page's title, H1 tags, meta description, presence of relevant keywords, domain name, and overall text content.
    A score is assigned based on these checks, with higher scores indicating a higher likelihood of the website being official.

    Args:
        event_name: The name of the event (e.g., "Tour de France").
        url: The URL of the website to verify.

    Returns:
        A dictionary containing the verification results:
        - event_name: The name of the event.
        - url: The URL of the website that was checked.
        - title: The title of the webpage.
        - score: The calculated score indicating the likelihood of the website being official.
        - keyword_hits: The number of relevant keywords found on the page.
        - h1_matches: A list of the first three H1 tags found on the page.
        - error: If an error occurred during the request, this key will contain the error message.
        If an error occurs during the request, the function returns a dictionary with an error message and a score of -10.
    """
    score = 0
    keywords = ["official", "schedule", "results", "organizer", "press", "news", "media"]

    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except Exception as e:
        return {"error": str(e), "score": -10}

    soup = BeautifulSoup(response.text, 'html.parser')
    text = soup.get_text(separator=' ', strip=True).lower()

    # Normalize event name for comparison
    event_name_lower = event_name.lower()

    # Title check
    title = soup.title.string.lower() if soup.title else ""
    if event_name_lower in title:
        score += 2

    # H1 tags check
    h1_matches = [h.get_text().lower() for h in soup.find_all('h1')]
    if any(event_name_lower in h for h in h1_matches):
        score += 2

    # Meta description check
    meta_desc = soup.find("meta", attrs={"name": "description"}) or soup.find(
        "meta", attrs={"property": "og:description"}
    )
    if meta_desc and event_name_lower in meta_desc.get("content", "").lower():
        score += 1

    # Keyword presence in full text
    keyword_hits = sum(1 for kw in keywords if kw in text)
    score += keyword_hits  # +1 per keyword found

    # Domain name heuristic
    domain = urlparse(url).netloc.lower()
    if any(part in domain for part in event_name_lower.replace("de", "").split()):
        score += 1

    # Presence of event name in full text
    if event_name_lower in text:
        score += 2

    # Final results
    return {
        "event_name": event_name,
        "url": url,
        "title": title,
        "score": score,
        "keyword_hits": keyword_hits,
        "h1_matches": h1_matches[:3],  # Just a sample
    }


def get_wikipedia_url(tour_name):
    """Search Google for the Wikipedia page of the tour."""
    query = f"{tour_name} site:wikipedia.org"
    ddgs = DDGS()
    for result in ddgs.text(query, max_results=5):
    # for result in search.text(query):
        if "wikipedia.org" in result:
            return result
    return None


def extract_official_website(wiki_url):
    """Extract the official website from the Wikipedia page."""
    response = requests.get(wiki_url, headers={"User-Agent": "Mozilla/5.0"})
    if response.status_code != 200:
        return None
    url_all = []
    soup = BeautifulSoup(response.text, "html.parser")

    # Search the infobox first for the official website
    infobox = soup.find("table", class_="infobox")
    if infobox:
        for a in infobox.find_all("a", href=True):
            if a["href"].startswith("http") and "official website" in a.get_text().lower():
                url_all.append(a["href"])

    # If not found in the infobox, search the whole page for links with "official website"
    for a in soup.find_all("a", href=True):
        if "official website" in a.get_text().lower() and a["href"].startswith("http"):
            return a["href"]

    # Fallback: Check for possible external links section
    external_links_section = soup.find("span", {"id": "External_links"})
    if external_links_section:
        parent = external_links_section.find_parent("h2")
        if parent:
            for link in parent.find_next("ul").find_all("a", href=True):
                if "official website" in link.get_text().lower() and link["href"].startswith("http"):
                    url_all.append(link["href"])

    return url_all


@tool
def get_official_website(tour_name: str) -> list:
    """
    Get the official website of a cycling tour.
    Args:
        tour_name: The name of the cycling tour.
    Returns:
        url of official website
    """
    wiki_url = get_wikipedia_url(tour_name)
    if wiki_url:
        return extract_official_website(wiki_url)
    return []
    # "Not Found"


if __name__ == '__main__':
    import json
    with open("../tourname.json", "r") as f:
        cycling_tours = json.load(f)
    official_websites = {tour: get_official_website(tour) for tour in cycling_tours}
    # print(official_websites)
    for key, val in official_websites.items():
        print(json.dumps(verify_event_website(key, val), indent=4))
    with open("../tourname_data.json", "w+") as f:
        json.dump(verify_event_website, f, indent=4)

    # model = LiteLLMModel(model_id="bedrock/us.meta.llama3-3-70b-instruct-v1:0")
    #
    # agent = CodeAgent(
    #     tools=[get_official_website],
    #     model=model,
    #     additional_authorized_imports=["helium"],
    #     max_steps=20,
    #     verbosity_level=2,
    # )
    # search_request = """
    #     Please navigate to search engine to find the event Santos Tour Down Under official website and give me the official website url.
    #     """
    #
    # agent_output = agent.run(search_request)
    # print("Final output:")
    # print(agent_output)
