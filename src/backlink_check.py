from urllib.parse import urlparse
import tldextract
from googlesearch import search
import time
import urllib.error
import googlesearch
import os
from dotenv import load_dotenv
from serpapi import GoogleSearch
import requests
from bs4 import BeautifulSoup

load_dotenv()
import json
import re
from duckduckgo_search import DDGS
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
from urllib.parse import urlparse
from fake_useragent import UserAgent

from urllib.parse import urlparse, parse_qs
from smolagents import tool
from src import search_function

def get_domain(url):
    parsed_url = urlparse(url)
    return parsed_url.netloc


def get_main_domain(url):
    extracted = tldextract.extract(url)
    return f"{extracted.domain}.{extracted.suffix}"


@tool
def verify_url(url_to_check: str, provider: str = "serperapi") -> list:
    """
    Verify if a URL appears in search results that link to Domain.
    Args:
        url_to_check: The URL to check
        provider: The search engine provider to use (default is "serperapi")
    Returns:
        A list of URLs found in the search results
    """
    # List to store search result URLs
    search_results = []
    domain_url = get_domain(url_to_check)
    # Search Google for the URL
    query = f'"intext:{domain_url} -site:{domain_url}"'
    print(f"Searching for: {query}")

    try:
        for result in search(
            query, stop=10, pause=2, extra_params={'filter': '1'}, user_agent=googlesearch.get_random_user_agent()
        ):
            search_results.append(result)
            # Check the number of results (this could be improved to check for reputable sites)
            if len(search_results) >= 5:  # Threshold can be adjusted
                print(f"URL appears {len(search_results)} times, which is a good sign!")
                return search_results
        else:
            print(f"URL appears {len(search_results)} times, which might not be enough.")
            return search_results
    except urllib.error.HTTPError:
        print("HTTPError: Too many requests. try API")
        if provider == "serperapi":
            search_results = search_function.search_serper(domain_url)
        else:
            search_results = search_function.search_serp(domain_url)
    return search_results


def get_seo_backlinks(target_url, max_results=100, delay=2):
    """
    Find backlinks to a website using DuckDuckGo for SEO analysis.

    Args:
        target_url (str): Target URL or domain to check backlinks for
        max_results (int): Maximum number of backlinks to retrieve
        delay (int): Delay between requests in seconds

    Returns:
        list: List of dictionaries containing backlink information
    """
    # Normalize the target URL
    if not target_url.startswith(('http://', 'https://')):
        target_url = 'https://' + target_url

    # Extract domain from URL
    domain = urlparse(target_url).netloc
    if domain.startswith('www.'):
        domain = domain[4:]

    # Create search query for backlinks
    query = f'{domain} -site:{domain}'
    encoded_query = urllib.parse.quote(query)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://duckduckgo.com/',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }

    backlinks = []
    results_per_page = 25
    max_pages = (max_results + results_per_page - 1) // results_per_page

    print(f"Searching for backlinks to: {domain}")
    print(f"Query: {query}")

    for page in range(max_pages):
        start_index = page * results_per_page
        search_url = f"https://html.duckduckgo.com/html/?q={encoded_query}&s={start_index}"
        print(search_url)
        try:
            print(f"Fetching results page {page + 1}...")
            response = requests.get(search_url, headers=headers)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Find all search results
            results = soup.find_all('div', class_='result__body')

            if not results:
                print("No more results found.")
                break

            for result in results:
                try:
                    # Extract title
                    title_elem = result.find('a', class_='result__a')
                    title = title_elem.get_text().strip() if title_elem else "No Title"

                    # Extract URL
                    url_elem = result.find('a', class_='result__url')
                    if not url_elem:
                        continue

                    # Handle DuckDuckGo URL format
                    raw_url = url_elem.get('href', '')
                    if '/rd/' in raw_url or '/l/' in raw_url:
                        # Parse and decode the actual URL from DuckDuckGo's redirect
                        parsed = urlparse(raw_url)
                        if 'uddg' in parse_qs(parsed.query):
                            actual_url = parse_qs(parsed.query)['uddg'][0]
                        else:
                            # Try to extract from path
                            match = re.search(r'uddg=([^&]+)', raw_url)
                            if match:
                                actual_url = urllib.parse.unquote(match.group(1))
                            else:
                                actual_url = raw_url
                    else:
                        actual_url = raw_url

                    # Clean and normalize URL
                    parsed_url = urlparse(actual_url)
                    linking_domain = parsed_url.netloc

                    # Skip if the linking domain is the same as target domain
                    if linking_domain == domain or linking_domain == 'www.' + domain:
                        continue

                    # Extract snippet/description
                    snippet_elem = result.find('a', class_='result__snippet')
                    snippet = snippet_elem.get_text().strip() if snippet_elem else "No description"

                    # Add to backlinks list
                    backlink_info = {'title': title, 'url': actual_url, 'domain': linking_domain, 'snippet': snippet}

                    backlinks.append(backlink_info)

                    # Check if we've reached the maximum requested results
                    if len(backlinks) >= max_results:
                        break

                except Exception as e:
                    print(f"Error processing result: {e}")
                    continue

            # Check if we've reached the maximum requested results
            if len(backlinks) >= max_results:
                break

            # Add delay between pages to avoid rate limiting
            time.sleep(delay)

        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            break

    return backlinks


def analyze_backlinks(backlinks):
    """Analyze backlinks for SEO insights"""
    if not backlinks:
        return {}

    # Count domains
    domain_counts = {}
    for backlink in backlinks:
        domain = backlink['domain']
        domain_counts[domain] = domain_counts.get(domain, 0) + 1

    # Sort domains by count
    top_domains = sorted(domain_counts.items(), key=lambda x: x[1], reverse=True)

    analysis = {
        'total_backlinks': len(backlinks),
        'unique_domains': len(domain_counts),
        'top_referring_domains': top_domains[:10],
    }

    return analysis


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




def verify_url_selenium(url_to_check, threshold=3):
    domain_url = get_domain(url_to_check)
    query = f'{domain_url} -site:{domain_url}'
    print(query)
    ua = UserAgent()
    user_agent = ua.random

    options = Options()
    options.add_argument("--headless")  # Run in headless mode
    options.add_argument(f"user-agent={user_agent}")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    # search_url = f"https://www.google.com/search?q={query}"=
    search_url = f"https://html.duckduckgo.com/html/?q={query}"
    print(f"Searching for: {search_url}")
    driver.get(search_url)

    search_results = []
    results_per_page = 10
    max_pages = (threshold + results_per_page - 1) // results_per_page
    time.sleep(5)  # Wait for the page to load
    for page in range(max_pages):
        results = driver.find_elements(By.CSS_SELECTOR, 'div')
        print(results)
        if not results:
            print("No more results found.")
            break
        for result in results:
            link = result.find_element(By.TAG_NAME, 'a').get_attribute('href')
            if domain_url in link:
                search_results.append(link)
                if len(search_results) >= threshold:
                    driver.quit()
                    return True

        next_button = driver.find_element(By.CSS_SELECTOR, 'a.result--more__btn')
        if next_button:
            next_button.click()
            time.sleep(2)  # Add delay to avoid rate limiting
        else:
            break

    driver.quit()
    return len(search_results) >= threshold





if __name__ == '__main__':
    url_to_check = "https://c1aude.ai/"
    threshold = 3
    out = verify_url(url_to_check)
    print(out)
    print(len(out))
    if len(out) >= 10:
        print(f"The URL {url_to_check} appears at least {threshold} times in search results.")
    else:
        print(f"The URL {url_to_check} does not appear at least.")
