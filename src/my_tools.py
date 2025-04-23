import os

import requests
from bs4 import BeautifulSoup

from pathlib import Path
from smolagents import Tool, tool, ToolCollection, CodeAgent
from mcp import StdioServerParameters
import datasets
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.retrievers import BM25Retriever


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
    name: str = "get_rout_information_cities_list"
    description: str = "Get a dictionary of information of the route between city to other city in order."
    inputs = {
        "city_names": {
            "type": "array",
            "description": "A list of city names with country to get road names between city to city in order.",
        },
    }
    output_type = "any"


    def setup(self):
        self.map_util = map_utility.MapUtility()


    def forward(self, city_names: list[str]) -> list:
        """
        Args:
            city_names: A list of city names with country for handle route name duplicate to get road names between city to city in order.
        Returns:
            A dictionary containing the road names between the specified cities.
            example:
            {
            "map": m,
            "segments": all_segments,
            "total_distance": total_distance,
            "total_road_names": all_road,
        }
        """
        waypoints = [(self.map_util.get_city_coords(city)) for city in city_names]
        result = self.map_util.get_multi_waypoint_route(waypoints, max_routes_per_segment=3)
        result = result.get("total_road_names", [])
        return result


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


class RetrieverTool(Tool):
    name = "retriever"
    description = "Uses semantic search to retrieve the parts of transformers documentation that could be most relevant to answer your query."
    inputs = {
        "query": {
            "type": "string",
            "description": "The query to perform. This should be semantically close to your target documents. Use the affirmative form rather than a question.",
        }
    }
    output_type = "string"

    def __init__(self, docs, **kwargs):
        super().__init__(**kwargs)
        self.retriever = BM25Retriever.from_documents(
            docs, k=10
        )

    def forward(self, query: str) -> str:
        assert isinstance(query, str), "Your search query must be a string"

        docs = self.retriever.invoke(
            query,
        )
        return "\nRetrieved documents:\n" + "".join(
            [
                f"\n\n===== Document {str(i)} =====\n" + doc.page_content
                for i, doc in enumerate(docs)
            ]
        )



if __name__ == '__main__':
    knowledge_base = datasets.load_dataset("m-ric/huggingface_doc", split="train[:10]")
    knowledge_base = knowledge_base.filter(lambda row: row["source"].startswith("huggingface/transformers"))
    source_docs = [
        Document(page_content=doc["text"], metadata={"source": doc["source"].split("/")[1]})
        for doc in knowledge_base
    ]
    print(source_docs)

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        add_start_index=True,
        strip_whitespace=True,
        separators=["\n\n", "\n", ".", " ", ""],
    )
    docs_processed = text_splitter.split_documents(source_docs)
    print("Number of documents:", len(docs_processed))

    retriever_tool = RetrieverTool(docs_processed)
    print(retriever_tool.forward("How to use the pipeline function?"))