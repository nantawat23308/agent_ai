import json
import os
import socket
import ssl
from urllib.parse import urlparse

import requests
import tldextract
import whois
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from duckduckgo_search import DDGS
from requests.exceptions import HTTPError, Timeout, RequestException
from serpapi import GoogleSearch

load_dotenv()
from src import my_tools
from src import url_phase
from src import backlink_check
from src import search_function

def verify_event_website(event_name, url):
    score = 0
    details = {}

    # Normalize inputs
    event_name_lower = event_name.lower()
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except HTTPError as http_err:
        if response.status_code == 403:
            details = {"error": "Access forbidden: 403 Forbidden", "score": -10}
        elif response.status_code == 404:
            details = {"error": "Page not found: 404 Not Found", "score": -10}
        elif response.status_code == 500:
            details = {"error": "Server error: 500 Internal Server Error", "score": -10}
        else:
            details = {"error": f"HTTP error occurred: {http_err}", "score": -10}
    except Timeout as timeout_err:
        details = {"error": f"Request timed out: {timeout_err}", "score": -10}
    except RequestException as req_err:
        details = {"error": f"Request error occurred: {req_err}", "score": -10}
    except Exception as e:
        details = {"error": f"An error occurred: {e}", "score": -10}

    domain_parts = tldextract.extract(url)
    domain = domain_parts.domain + '.' + domain_parts.suffix
    if any(part in domain.lower() for part in event_name_lower.replace("de", "").split()):
        score += 1
    details["domain"] = domain

    # WHOIS
    try:
        w = whois.whois(domain)
        if w and any(
            event_name_lower in str(v).lower() for v in [w.get('org'), w.get('name'), w.get('registrant_name')]
        ):
            score += 2
            details["whois_org"] = w.get('org')
    except:
        details["whois_org"] = "N/A"

    # SSL Cert Org
    ssl_org = get_ssl_organization(domain)
    if ssl_org and event_name_lower in ssl_org.lower():
        score += 2
    details["ssl_org"] = ssl_org

    ranking = google_search_ranking_serper(event_name, url)
    if ranking and ranking <= 10:  # If the URL appears in the top 10 results
        score += 3  # High rank boosts the score
    details["google_search_rank"] = ranking if ranking else "Not found in top 10"

    # Wikipedia Backlink Check - Optional (stub)
    # Could use a Wikipedia API or scraper to see if the URL appears on the event's page
    score += wikipedia_link_score(event_name, url)

    # Backlink Check
    backlinks = backlink_check.verify_url(url)
    if backlinks:
        score += 1
    details["backlinks"] = backlinks

    # Final trust score
    details["event_name"] = event_name
    details["url"] = url
    details["score"] = score

    return details


def get_ssl_organization(domain):
    try:
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(socket.socket(), server_hostname=domain) as s:
            s.settimeout(5.0)
            s.connect((domain, 443))
            cert = s.getpeercert()
            return cert.get('subject', [[('', '')]])[0][1]  # Org name
    except:
        return None


def get_structured_data(soup):
    json_ld = soup.find_all("script", type="application/ld+json")
    structured = []
    for tag in json_ld:
        try:
            data = json.loads(tag.string)
            if isinstance(data, dict) and "SportsEvent" in str(data.get("@type", "")):
                structured.append(data)
        except:
            continue
    return structured


def google_search_ranking(event_name, url):
    """
    This function checks the Google search ranking of a specific URL when searching for the event_name.

    Args:
        event_name (str): The name of the event (e.g., "Tour de France").
        url (str): The official event URL (e.g., "https://www.letour.fr/en/").

    Returns:
        int: The ranking of the URL in the search results (1-based).
    """
    search_params = {
        "q": f"{event_name} Official Website",  # Search for the event name
        "api_key": os.getenv("SERPER_API_KEY"),
    }

    # Perform the search using SerpAPI
    search = GoogleSearch(search_params)
    search_results = search.get_dict()
    # Extract the domain from the provided URL
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.lower()
    redirected_url = url_phase.check_redirection(url)
    redirected_domain = urlparse(redirected_url).netloc.lower()
    # Check if either the original or redirected domain appears in the search results

    print(search_results)
    for index, result_dic in enumerate(search_results.get('organic_results', [])):
        if 'link' in result_dic:
            # print(f"Checking {result_dic['link']}")
            result_url = url_phase.check_redirection(result_dic['link'])
            result_domain = urlparse(result_url).netloc.lower()

            # If either the original or redirected domain matches
            if domain in result_domain or redirected_domain in result_domain:
                return index + 1  # Return 1-based index (ranking)

    return None  # URL not found in the top results

def google_search_ranking_serper(event_name, url):
    """
    This function checks the Google search ranking of a specific URL when searching for the event_name.

    Args:
        event_name (str): The name of the event (e.g., "Tour de France").
        url (str): The official event URL (e.g., "https://www.letour.fr/en/").

    Returns:
        int: The ranking of the URL in the search results (1-based).
    """

    # Perform the search using SerpAPI
    query = f"{event_name} Official Website"
    search = search_function.query_serper(query)
    search_results = search
    # Extract the domain from the provided URL
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.lower()
    redirected_url = url_phase.check_redirection(url)
    redirected_domain = urlparse(redirected_url).netloc.lower()
    # Check if either the original or redirected domain appears in the search results
    for index, result_dic in enumerate(search_results.get('organic', [])):
        if 'link' in result_dic:
            # print(f"Checking {result_dic['link']}")
            result_url = url_phase.check_redirection(result_dic['link'])
            result_domain = urlparse(result_url).netloc.lower()

            # If either the original or redirected domain matches
            if domain in result_domain or redirected_domain in result_domain:
                return index + 1  # Return 1-based index (ranking)

    return None  # URL not found in the top results


def get_wikipedia_external_links(url_wiki):
    response = requests.get(url_wiki)
    response.raise_for_status()
    if response.status_code != 200:
        print("Failed to fetch Wikipedia page")
        return {}
    soup = BeautifulSoup(response.text, 'html.parser')
    table_sections = []
    infobox = soup.find("table", class_="infobox")
    if infobox:
        # for b in infobox.find_all("td", class_="infobox-data"):
        for tr in infobox.find_all("tr"):
            for th in tr.find_all("th", class_="infobox-label"):
                if "Web site" in th.text:
                    table_sections.append(url_phase.check_redirection(tr.a.get("href")))

    # Extract external links
    ext_links = []
    external_span = soup.find(id="External_links").find_all_next("span", class_="official-website")
    for ext_a in external_span:
        for a in ext_a.find_all("a", href=True):
            ext_links.append(url_phase.check_redirection(a.get("href")))
    return {"table_sections": table_sections, "external_links": ext_links}


def calculate_weighted_score(external_links, table_sections, url):
    """
    Calculate a weighted score for the URL based on its presence in specific sections.

    Args:
        external_links (list): List of external links found on the Wikipedia page.
        table_sections (list): List of sections in the Wikipedia article.
        url (str): The URL to check for.

    Returns:
        float: A weighted score based on the occurrence and section importance.
    """
    score = 0
    table_freq = table_sections.count(url.lower())
    score += table_freq * 3.0
    frequency = external_links.count(url.lower())  # Count how many times the URL appears
    score += frequency * 1.0  # Weighted score by frequency and section
    return score


def wikipedia_link_score(tour_name, url):
    data = None
    wiki_url = get_wikipedia_url(tour_name)
    if wiki_url:
        data = get_wikipedia_external_links(wiki_url)
    if not data:
        return 0.0

    external_links = data.get("external_links", [])
    table_sections = data.get("table_sections", [])

    return calculate_weighted_score(external_links, table_sections, url.lower())


def extract_official_website(wiki_url: str) -> str | None:
    """Extract the official website from the Wikipedia page."""
    response = requests.get(wiki_url, headers={"User-Agent": "Mozilla/5.0"})
    if response.status_code != 200:
        return None
    soup = BeautifulSoup(response.text, "html.parser")

    # Search the infobox first for the official website
    infobox = soup.find("table", class_="infobox")
    if infobox:
        for a in infobox.find_all("a", href=True):
            if a["href"].startswith("http") and "official website" in a.get_text().lower():
                return url_phase.check_redirection(a["href"])

    # If not found in the infobox, search the whole page for links with "official website"
    for a in soup.find_all("a", href=True):
        if "official website" in a.get_text().lower() and a["href"].startswith("http"):
            return url_phase.check_redirection(a["href"])

    # Fallback: Check for possible external links section
    external_links_section = soup.find("span", {"id": "External_links"})
    if external_links_section:
        parent = external_links_section.find_parent("h2")
        if parent:
            for link in parent.find_next("ul").find_all("a", href=True):
                if "official website" in link.get_text().lower() and link["href"].startswith("http"):
                    return url_phase.check_redirection(link["href"])

    return None

def get_wikipedia_url(query):
    """Search Google for the Wikipedia page of name."""
    query = f"{query} site:wikipedia.org"
    ddgs = DDGS()
    for result in ddgs.text(query, max_results=5):
        # for result in search(query, pause=5):
        if "wikipedia.org" in result.get('href'):
            return result.get('href')
    return None

def get_official_website(tour_name: str) -> str:
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
    return "Not Found"
    # "Not Found"

# Example use
if __name__ == "__main__":
    print(google_search_ranking_serper("Benelux tour", "https://renewitour.com/en/"))
    # ver_dict = verify_event_website("Benelux Tour", "https://renewitour.com/nl/")
    # for k, v in ver_dict.items():
    #     print(f"{k}: {v}")
    # score = wikipedia_link_score("Tour de France", "https://www.letour.fr/en/")
    # print(score)
