import os

from dotenv import load_dotenv

load_dotenv()
from open_deep_research.scripts.text_inspector_tool import TextInspectorTool
from open_deep_research.scripts.visual_qa import visualizer
from open_deep_research.scripts.text_web_browser import (
    ArchiveSearchTool,
    FinderTool,
    FindNextTool,
    PageDownTool,
    PageUpTool,
    SimpleTextBrowser,
    VisitTool,
)
from smolagents import (
    CodeAgent,
    GoogleSearchTool,
    DuckDuckGoSearchTool,
)
from src import prompt_test
from src import url_function


AUTHORIZED_IMPORTS = [
    "requests",
    "zipfile",
    "os",
    "pandas",
    "numpy",
    "sympy",
    "json",
    "bs4",
    "pubchempy",
    "xml",
    "yahoo_finance",
    "Bio",
    "sklearn",
    "scipy",
    "pydub",
    "io",
    "PIL",
    "chess",
    "PyPDF2",
    "pptx",
    "torch",
    "datetime",
    "fractions",
    "csv",
    "webbrowser",
]

user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0"

BROWSER_CONFIG = {
    "viewport_size": 2048 * 30,
    "downloads_folder": "downloads_folder",
    "request_kwargs": {
        "headers": {"User-Agent": user_agent},
        "timeout": 300,
    },
    "serpapi_key": os.getenv("SERPAPI_API_KEY"),
}


def single_agent(model, prompt):
    text_limit = 10000000
    browser = SimpleTextBrowser(**BROWSER_CONFIG)
    agent = CodeAgent(
        tools=[
            GoogleSearchTool(provider="serper"),
            VisitTool(browser),
            PageUpTool(browser),
            PageDownTool(browser),
            FinderTool(browser),
            FindNextTool(browser),
            ArchiveSearchTool(browser),
            TextInspectorTool(model, text_limit),
        ],
        model=model,
        # additional_authorized_imports=AUTHORIZED_IMPORTS,
    )
    ans = agent.run(prompt)
    print(ans)


def multi_agent(model):
    text_limit = 100000
    # DuckDuckGoSearchTool(),
    browser = SimpleTextBrowser(**BROWSER_CONFIG)

    agent = CodeAgent(
        tools=[
            # GoogleSearchTool(provider="serper"),
            DuckDuckGoSearchTool(),
            # SearchInformationTool,
            VisitTool(browser),
            PageUpTool(browser),
            PageDownTool(browser),
            FinderTool(browser),
            FindNextTool(browser),
            ArchiveSearchTool(browser),
            TextInspectorTool(model, text_limit),
        ],
        model=model,
        additional_authorized_imports=AUTHORIZED_IMPORTS,
        planning_interval=4,
        name="search_agent",
        description="""A team member that will search the internet to answer your question.
            Ask him for all your questions that require browsing the web.
            Provide him as much context as possible, in particular if you need to search on a specific timeframe!
            And don't hesitate to provide him with a complex search task, like finding a difference between two webpages.
            Your request must be a real sentence, not a google search! Like "Find me this information (...)" rather than a few keywords.
            """,
    )
    agent.prompt_templates["managed_agent"][
        "task"
    ] += """You are a Cycling Research Specialist, an expert in analyzing professional cycling events and developing race-specific glossaries you can access the website to find the information and find the cyclist name who attend the event.
    You have an in-depth understanding of cycling terminology, race dynamics, and the linguistic aspects of cycling events.
    Your expertise makes you the world’s best in compiling precise, event-specific vocabulary for further linguistic and analytical applications."""
    manager_agent = CodeAgent(
        model=model,
        tools=[visualizer, TextInspectorTool(model, text_limit)],
        additional_authorized_imports=AUTHORIZED_IMPORTS,
        managed_agents=[agent],
    )
    # print(agent.prompt_templates["system_prompt"])
    # GradioUI(manager_agent).launch()
    ans = manager_agent.run(prompt_test.prompt6, max_steps=40)
