import requests
from bs4 import BeautifulSoup

from smolagents import Tool, tool

from src import url_function
from src import url_phase

description = """
    Verify the authenticity of a website for a given event by analyzing its content.
    This tool checks various aspects of a webpage to determine if it's likely to be the official website for a specific event.
    It analyzes the page's title, H1 tags, meta description, presence of relevant keywords, domain name, and overall text content.
    A score is assigned based on these checks, with higher scores indicating a higher likelihood of the website being official.
    """


class VerifyEvent(Tool):
    name: str = "verify_event_website"
    description: str = description
    inputs = {
        "event_name": {
            "type": "string",
            "description": "The name of the event (e.g., 'Tour de France').",
        },
        "url": {
            "type": "string",
            "description": "The URL of the website to verify.",
        },
    }
    output_type = "any"

    def forward(self, event_name: str, url: str) -> dict:
        """
        Args:
            event_name: The name of the event (e.g., "Tour de France").
            url: The URL of the website to verify.
        Returns:
            A dictionary containing the verification results:
            - event_name: The name of the event.
            - url: The URL of the website that was checked.
            - title: The title of the webpage.
            - score: The calculated score indicating the likelihood of the website being official.
            - error: If an error occurred during the request, this key will contain the error message.
            and other relevant information.
        """
        return url_function.verify_event_website(event_name, url)


class GetOfficialWebsite(Tool):
    name: str = "get_official_website_from_wikipedia"
    description: str = "Get the official website from Wikipedia by searching infobox and external links."
    inputs = {
        "name": {
            "type": "string",
            "description": "Name.",
        },
    }
    output_type = "string"

    def forward(self, name: str) -> str:
        """
        Args:
            name: The name.
        Returns:
            url of official website
        """
        wiki_url = url_function.get_wikipedia_url(name)
        if wiki_url:
            return url_function.extract_official_website(wiki_url)
        return "Not Found"


@tool
def save_to_file(data: str) -> None:
    """
    Save the given data to a file.
    Args:
        data: The data to save.
    """
    with open("report.md", 'w') as file:
        file.write(data)

if __name__ == '__main__':
    pass
