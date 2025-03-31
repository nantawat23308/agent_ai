import requests
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

def verify_event_website(event_name, url):
    score = 0
    details = {}

    # Normalize inputs
    event_name_lower = event_name.lower()
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except Exception as e:
        return {"error": f"Failed to load site: {e}", "score": -10}

    soup = BeautifulSoup(response.text, 'lxml')
    text = soup.get_text(separator=' ', strip=True).lower()

    # Title
    title = soup.title.string.lower() if soup.title else ""
    if fuzz.partial_ratio(event_name_lower, title) > 80:
        score += 2
    details["title"] = title

    # H1
    h1_tags = [h.get_text().lower() for h in soup.find_all('h1')]
    if any(fuzz.partial_ratio(event_name_lower, h) > 80 for h in h1_tags):
        score += 2
    details["h1_tags"] = h1_tags

    # Meta
    meta_tag = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
    meta_desc = meta_tag.get("content", "").lower() if meta_tag else ""
    if fuzz.partial_ratio(event_name_lower, meta_desc) > 80:
        score += 1
    details["meta_description"] = meta_desc

    # Keyword relevance
    keywords = ["official", "schedule", "results", "organizer", "press", "news", "media", "tickets"]
    keyword_hits = sum(1 for kw in keywords if kw in text)
    score += keyword_hits
    details["keyword_hits"] = keyword_hits

    # Domain relevance
    domain_parts = tldextract.extract(url)
    domain = domain_parts.domain + '.' + domain_parts.suffix
    if any(part in domain.lower() for part in event_name_lower.replace("de", "").split()):
        score += 1
    details["domain"] = domain

    # Full text fuzzy match
    if fuzz.partial_ratio(event_name_lower, text) > 80:
        score += 2

    # WHOIS
    try:
        w = whois.whois(domain)
        if w and any(event_name_lower in str(v).lower() for v in [w.get('org'), w.get('name'), w.get('registrant_name')]):
            score += 2
            details["whois_org"] = w.get('org')
    except:
        details["whois_org"] = "N/A"

    # SSL Cert Org
    ssl_org = get_ssl_organization(domain)
    if ssl_org and event_name_lower in ssl_org.lower():
        score += 2
    details["ssl_org"] = ssl_org

    # Structured Data
    structured = get_structured_data(soup)
    if structured:
        score += 1
    details["structured_data_found"] = bool(structured)

    # Wikipedia Backlink Check - Optional (stub)
    # Could use a Wikipedia API or scraper to see if the URL appears on the event's page

    # Final trust score
    details["event_name"] = event_name
    details["url"] = url
    details["score"] = score

    return details


def google_search_ranking(event_name):
    search_params = {
        "q": event_name,
        "api_key": os.getenv("SERPER_API_KEY")
    }

    search = GoogleSearch(search_params)
    results = search.get_dict()

    for index, result in enumerate(results.get('organic_results', [])):
        if 'link' in result and event_name.lower() in result['link'].lower():
            return index + 1  # Return ranking (1-indexed)

    return None  # URL not found in top results



# Example use
if __name__ == "__main__":
    result = verify_event_website("Tour de France", "https://www.letour.fr/en/")
    for k, v in result.items():
        print(f"{k}: {v}")