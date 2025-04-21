import requests
from bs4 import BeautifulSoup

from pathlib import Path
from smolagents import Tool, tool

from src import url_function
from src import url_phase
from src import map_function
from huggingface_hub import list_models
from src import map_utility
from src import mdconvert
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
    report_folder = Path("report")
    report_folder.mkdir(parents=True, exist_ok=True)
    with open(report_folder.joinpath("report.md"), 'w+') as file:
        file.write(data)

@tool
def model_download_tool(task: str) -> str:
    """
    Download a model from Hugging Face.
    Args:
        task: The task for which to find the most downloaded model.
    Returns:
        The model ID of the most downloaded model for the specified task.
    """
    most_downloaded_model = next(iter(list_models(filter=task, sort="downloads", direction=-1)))
    return most_downloaded_model.modelId


class RoadNameTool(Tool):
    name: str = "get_road_name_from_city"
    description: str = "Get the road name from a given city."
    inputs = {
        "city": {
            "type": "string",
            "description": "The name of the city.",
        },
    }
    output_type = "any"


    def __init__(self):
        super().__init__()
        self.map_util = map_utility.MapUtility()
        self.map_util.visualize = False


    def setup(self):
        pass


    def forward(self, city: list[str]) -> dict:
        """
        Args:
            city: The name of the city.
        Returns:
            The road name associated with the city.
        """
        self.map_util.locations = city
        return self.map_util.get_route_city()


class MarkDownFromURL(Tool):
    name: str = "generate_markdown_from_url"
    description: str = "Generate a markdown file from a given URL."
    inputs = {
        "url": {
            "type": "string",
            "description": "The URL to generate markdown from.",
        },
    }
    output_type = "string"

    def forward(self, url: str) -> str:
        """
        Args:
            url: The URL to generate markdown from.
        Returns:
            The generated markdown content.
        """
        return url_phase.generate_markdown(url)
class MarkdownConverterTool(Tool):
    name: str = "markdown_converter"
    description: str = "Convert a file to markdown format."
    inputs = {
        "file_path": {
            "type": "string",
            "description": "The path to the file to convert.",
        },
    }
    output_type = "string"

    def forward(self, url: str) -> str:
        """
        Args:
            file_path: The path to the file to convert.
        Returns:
            The converted markdown content.
        """
        converter = mdconvert.MarkdownConverter()
        response = requests.get(url)
        return converter.convert(response).text_content
if __name__ == '__main__':
    print(MarkdownConverterTool().forward("https://docs.litellm.ai/release_notes/v1.66.0-stable"))
