from dotenv import load_dotenv
import os
from phoenix.otel import register
from openinference.instrumentation.smolagents import SmolagentsInstrumentor

load_dotenv()
from open_deep_research.scripts.visual_qa import visualizer
from open_deep_research.scripts.text_inspector_tool import TextInspectorTool
from open_deep_research.scripts.text_web_browser import (
    ArchiveSearchTool,
    FinderTool,
    FindNextTool,
    PageDownTool,
    PageUpTool,
    SimpleTextBrowser,
    VisitTool,
    SearchInformationTool,
)
from smolagents import (
    CodeAgent,
    GoogleSearchTool,
    # HfApiModel,
    LiteLLMModel,
    DuckDuckGoSearchTool,
    ToolCallingAgent,
    VisitWebpageTool,
    PythonInterpreterTool,
    ManagedAgentPromptTemplate,
    PromptTemplates,
    PlanningPromptTemplate,
    FinalAnswerPromptTemplate,
)
import litellm
from src import prompt_test
from src import constants
from src import model_create
from src import agent as my_agent
from src import tool_me
from src import my_tools
from src import backlink_check

#
# litellm._turn_on_debug()
register()
# SmolagentsInstrumentor().instrument()


BROWSER_CONFIG = {
    "viewport_size": 2048 * 30,
    "downloads_folder": "downloads_folder",
    "request_kwargs": {
        "headers": {"User-Agent": constants.USER_AGENT},
        "timeout": 300,
    },
    "serpapi_key": os.getenv("SERPAPI_API_KEY"),
}

managed_agent = ManagedAgentPromptTemplate(task="", report="")
TEST_PROMPT = PromptTemplates(
    system_prompt="",
    planning=PlanningPromptTemplate(
        initial_facts="",
        initial_plan="",
        update_facts_pre_messages="",
        update_facts_post_messages="",
        update_plan_pre_messages="",
        update_plan_post_messages="",
    ),
    managed_agent=ManagedAgentPromptTemplate(task="Find Official URL", report="Official URL"),
    final_answer=FinalAnswerPromptTemplate(pre_messages="", post_messages=""),
)


class AgentM:
    def __init__(self):
        self.text_limit = 100000
        self.model = model_create.bedrock_model()
        self.browser = SimpleTextBrowser(**BROWSER_CONFIG)
        self.tools = [
            DuckDuckGoSearchTool(),
            PythonInterpreterTool(),
            VisitTool(self.browser),
            PageUpTool(self.browser),
            PageDownTool(self.browser),
            FinderTool(self.browser),
            FindNextTool(self.browser),
            ArchiveSearchTool(self.browser),
            TextInspectorTool(self.model, self.text_limit),
        ]

    def agent_url_validate(self):
        """
        Follow these steps carefully:
        ## Steps
        ### 1. Search for the Official Website
        - Look for the official domain by checking trusted sources such as Wikipedia, official social media accounts, and reputable news websites.
        - Prioritize domains with extensions like `.com`, `.org`, or country-specific domains used officially.

        ### 2. Verify the Website’s Authenticity
        - Check if the site is referenced on trusted sources (Wikipedia, major sports networks like ESPN, BBC Sport, etc.).
        - Ensure that the website belongs to the governing body or the official organizers of the tour.
        - Look for contact details, official press releases, or links from verified social media accounts.

        ### 3. Provide a Verified Response
        - If you confirm the official website, return the URL along with a brief justification (e.g., "This is the official website as listed on the sport’s governing body page.").
        - If no authoritative site is found, state that the information is unavailable rather than guessing.

        You are an intelligent research agent tasked with finding the official website of a given sport tour or league. Your goal is to ensure that the URL is authoritative and legitimate
        Follow these steps carefully:
        ## Steps
        ### 1. Search for the Official Website
        you can use get_official_website function to find official website
        in case you not found the official website from this tool you can use the search engine to find the official website

        ### 2. Verify the Website’s Authenticity
        you can use verify_event_website th verify how much score of this website to be the official website score should be above 7
        in case URL not pass you have to go back to step 1 to find other website

        ### 3. Provide a Verified Response
        - If you confirm the official website, return the URL along with a brief justification (e.g., "This is the official website as listed on the sport’s governing body page.").
        - If no authoritative site is found, state that the information is unavailable rather than guessing.

        :return:
        """
        # DuckDuckGoSearchTool()
        agent = CodeAgent(
            tools=[
                my_tools.get_official_website,
                # my_tools.verify_event_website,
                DuckDuckGoSearchTool(),
                my_tools.VerifyEvent(),
            ],
            model=self.model,
            max_steps=20,
            verbosity_level=2,
            name="URL_resolver",
            description="Validates and finds official URL",
            additional_authorized_imports=["requests", "bs4", "pandas", "os", "webbrowser", "json"],
        )
        agent.prompt_templates["managed_agent"][
            "task"
        ] += """You are an intelligent research agent tasked with finding the official website. Your goal is to ensure that the URL is authoritative and legitimate
        Follow these steps carefully:
        ## Steps
        ### 1. Search for the Official Website
        you can use {get_official_website} function to find official website
        in case you not found the official website from this tool you can use the search engine to find the official website

        ### 2. Verify the Website’s Authenticity
        you can use {verify_event_website} to verify how much score of this website you have to return only one which highest score and you think it is the official website.

        ### 3. Provide a Verified Response
        - If you confirm the official website, return the URL along with a brief justification (e.g., "This is the official website as listed on the sport’s governing body page.").
        - If no authoritative site is found, state that the information is unavailable rather than guessing.
          ## Output
        {"tour name": name of tour, "official website": url, "score": score}
        """

        return agent

    def agent_backlink(self):
        """
        You are an intelligent research agent tasked with finding the official website of a given sport tour or league. Your goal is to ensure that the URL is authoritative and legitimate

        :return:
        """
        agent = CodeAgent(
            tools=[
                # backlink_check.verify_url
                # DuckDuckGoSearchTool()
                GoogleSearchTool(provider="serperapi")
            ],
            model=self.model,
            max_steps=20,
            verbosity_level=2,
            name="backlink_agent",
            description="Research backlinks for a given URL",
            additional_authorized_imports=["requests", "bs4", "pandas", "os"],
        )
        agent.prompt_templates["managed_agent"][
            "task"
        ] += """
        You are an intelligent research agent tasked with finding the official website of a given sport tour or league. Your goal is to ensure that the URL is authoritative and legitimate
        """
        return agent

    def agent_web(self):
        agent = ToolCallingAgent(
            tools=self.tools,
            model=self.model,
            planning_interval=4,
            name="search_agent",
            description="""
            A team member that will search the internet to answer your question.
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
        return agent

    def agent_name(self):
        agent = CodeAgent(
            tools=[PythonInterpreterTool(), VisitWebpageTool()],
            model=self.model,
            additional_authorized_imports=["requests", "bs4", "pandas", "os"],
            max_steps=20,
            verbosity_level=2,
            description="""
            ## Webpage Name Verification for Sports Content  
            I want you to analyze the content of a given sports-related webpage and verify whether it contains names of people. Follow these steps:  
            
            1. **Extract** the text from the webpage.  
            2. **Identify** potential names using common name patterns, databases, or context clues.  
            3. **Cross-check** names with known sports players, coaches, and staff in relevant teams and leagues.  
            4. **Validate** the names by analyzing their surrounding context to differentiate between people, team names, and other entities.  
            5. **Determine** the associated **team, league, and region** if applicable.  
            6. **Classify** the names as active players, retired players, coaches, or other roles where possible.  
            7. **Output** a structured list of identified names, including:  
               - Full name  
               - Role (player, coach, referee, etc.)  
               - Team affiliation (if available)  
               - League/competition  
               - Region  
               - Confidence score for each identification  
            
            ### Additional Guidelines:  
            - **Exclude** generic terms, brand names, and non-human entities.  
            - **Differentiate** between team names and individual player names.  
            - **Handle abbreviations** (e.g., "CR7" → Cristiano Ronaldo, "LBJ" → LeBron James).  
            - If uncertain, provide reasoning for ambiguity.
            """,
        )
        return agent

    def agent_crawling(self):
        agent = CodeAgent(
            tools=[PythonInterpreterTool(), VisitWebpageTool(max_output_length=100000), DuckDuckGoSearchTool()],
            model=self.model,
            additional_authorized_imports=["requests", "bs4", "pandas", "os"],
            max_steps=20,
            verbosity_level=2,
            description="Web crawling and analyze contents.",
        )

        agent.prompt_templates["managed_agent"][
            "task"
        ] += """
                ## Webpage Name Verification for Sports Content  
                Crawl known or inferred pages like /teams or /participants.
                Extract names, teams, countries, sponsors based on context.
                Try to extract required data from the Website.

                I want you to analyze the content of a given sports-related webpage and verify whether it contains context what i want. Follow these steps:  

                1. **Extract** the text from the webpage no truncate the content.  
                2. **Identify** potential name using common name patterns, databases, or context clues.  
                3. **Cross-check** names with known sports players, coaches, and staff in relevant teams and leagues.  
                4. **Validate** the names by analyzing their surrounding context to differentiate between people, team names, and other entities.  
                5. **Determine** the associated **team, league, region, and other context** if applicable.  
                6. If some info (e.g. riders or sponsors) is missing, perform optimized Google searches: 
                e.g. "Tour de France 2025 riders site:wikipedia.org"
                7. **Output** a structured list, including context json format:  
                find of output should be MD contain
                Example
                    input: Full name
                    output: [{"Full name": ""}, {"Full name": ""}, ...]
                    input: 
                        Full name, Team, Region
                    output: 
                        [{"Full name": "", "Team": "", "Region": ""},
                        {"Full name": "", "Team": "", "Region": ""}, 
                        ...]

                ### Additional Guidelines:  
                - **Differentiate** between team names and individual player names.  
                - **Handle abbreviations** (e.g., "CR7" → Cristiano Ronaldo, "LBJ" → LeBron James).  
                """
        return agent

    def manage_agent(self, agent):
        """
        You are an expert Planning Agent tasked with solving problems efficiently through structured plans.
        Your job is:
        1. Analyze requests to understand the task scope
        2. Create a clear, actionable plan that makes meaningful progress with the `planning` tool
        3. Execute steps using available tools as needed
        4. Track progress and adapt plans when necessary
        5. Use `finish` to conclude immediately when the task is complete


        Available tools will vary by task but may include:
        - `planning`: Create, update, and track plans (commands: create, update, mark_step, etc.)
        - `finish`: End the task when complete
        Break tasks into logical steps with clear outcomes. Avoid excessive detail or sub-steps.
        Think about dependencies and verification methods.
        Know when to conclude - don't continue thinking once objectives are met.
        :param agent:
        :return:
        """

        manager_agent = CodeAgent(
            model=self.model,
            # tools=[visualizer, TextInspectorTool(self.model, self.text_limit)],
            tools=[visualizer],
            additional_authorized_imports=["time", "numpy", "pandas"],
            managed_agents=agent,
        )
        return manager_agent

    def run(self, task):
        # agent = self.agent_web()
        url_resolve_agent = self.agent_url_validate()
        back_link_agent = self.agent_backlink()
        manage_ag = self.manage_agent(
            [
                url_resolve_agent,
                # back_link_agent,
            ]
        )
        ans = manage_ag.run(task, max_steps=20)
        return ans


if __name__ == '__main__':
    agentic = AgentM()
    search_request = """Please find the OpenAI official website and give me the official website url."""

    # search_request = "please verify website https://www.letour.fr/en/ is the Real website not phishing by check other website are link to this website"
    # search_request = """https://www.nokerekoerse.be/en Is this the official website for the event Santos Tour Down Under?"""
    answer = agentic.run(search_request)
    print(answer)
