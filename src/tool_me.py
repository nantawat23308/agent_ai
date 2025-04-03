import requests
from requests.exceptions import HTTPError, Timeout, RequestException
from bs4 import BeautifulSoup
from fuzzywuzzy import fuzz
import tldextract
import whois
import ssl, socket, json
from urllib.parse import urlparse
import re
from serpapi import GoogleSearch
from dotenv import load_dotenv
import os

load_dotenv()
from src import my_tools
from src import url_phase
from src import backlink_check


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

    # soup = BeautifulSoup(response.text, 'lxml')
    # text = soup.get_text(separator=' ', strip=True).lower()

    # # Title
    # title = soup.title.string.lower() if soup.title else ""
    # if fuzz.partial_ratio(event_name_lower, title) > 80:
    #     score += 2
    # details["title"] = title
    #
    # # H1
    # h1_tags = [h.get_text().lower() for h in soup.find_all('h1')]
    # if any(fuzz.partial_ratio(event_name_lower, h) > 80 for h in h1_tags):
    #     score += 2
    # details["h1_tags"] = h1_tags
    #
    # # Meta
    # meta_tag = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
    # meta_desc = meta_tag.get("content", "").lower() if meta_tag else ""
    # if fuzz.partial_ratio(event_name_lower, meta_desc) > 80:
    #     score += 1
    # details["meta_description"] = meta_desc
    #
    # # Keyword relevance
    # keywords = ["official", "schedule", "results", "organizer", "press", "news", "media", "tickets"]
    # keyword_hits = sum(1 for kw in keywords if kw in text)
    # score += keyword_hits
    # details["keyword_hits"] = keyword_hits

    # # Structured Data
    # structured = get_structured_data(soup)
    # if structured:
    #     score += 1
    # details["structured_data_found"] = bool(structured)

    # # Full text fuzzy match
    # if fuzz.partial_ratio(event_name_lower, text) > 80:
    #     score += 2

    # Domain relevance
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

    ranking = google_search_ranking(event_name, url)
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
        "q": event_name,  # Search for the event name
        "api_key": os.getenv("SERPAPI_API_KEY") or os.getenv("SERPER_API_KEY"),
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
    for index, result_dic in enumerate(search_results.get('organic_results', [])):
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
    wiki_url = my_tools.get_wikipedia_url(tour_name)
    if wiki_url:
        data = get_wikipedia_external_links(wiki_url)
    if not data:
        return 0.0

    external_links = data.get("external_links", [])
    table_sections = data.get("table_sections", [])

    return calculate_weighted_score(external_links, table_sections, url.lower())


# Example use
if __name__ == "__main__":
    print(google_search_ranking("OpenAI", "https://openai.com/"))
    # ver_dict = verify_event_website("Benelux Tour", "https://renewitour.com/nl/")
    # for k, v in ver_dict.items():
    #     print(f"{k}: {v}")
    # score = wikipedia_link_score("Tour de France", "https://www.letour.fr/en/")
    # print(score)
