import os

from dotenv import load_dotenv
from mcp import StdioServerParameters

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
    DownloadTool
)
from smolagents import (
    CodeAgent,
    GoogleSearchTool,
    DuckDuckGoSearchTool,
    ToolCallingAgent,
    VisitWebpageTool,
    PythonInterpreterTool,
    ToolCollection,
)
from smolagents.mcp_client import MCPClient
from src import constants
from src import model_create
from src import my_tools
from src import prompt_test
import litellm
from phoenix.otel import register
from openinference.instrumentation.smolagents import SmolagentsInstrumentor

register()
SmolagentsInstrumentor().instrument()

litellm.drop_params=True
BROWSER_CONFIG = {
    "viewport_size": 2048 * 30,
    "downloads_folder": "downloads_folder",
    "request_kwargs": {
        "headers": {"User-Agent": constants.USER_AGENT},
        "timeout": 300,
    },
    "serpapi_key": os.getenv("SERPAPI_API_KEY"),
}





class AgentM:
    def __init__(self):
        self.text_limit = 100000
        # self.model = model_create.huggingface_model(model="meta-llama/Llama-4-Scout-17B-16E-Instruct")
        self.model = model_create.bedrock_model()
        self.browser = SimpleTextBrowser(**BROWSER_CONFIG)
        self.tools = [
            # DuckDuckGoSearchTool(),
            # PythonInterpreterTool(),
            SearchInformationTool(self.browser),
            VisitTool(self.browser),
            PageUpTool(self.browser),
            PageDownTool(self.browser),
            FinderTool(self.browser),
            FindNextTool(self.browser),
            ArchiveSearchTool(self.browser),
            TextInspectorTool(self.model, self.text_limit),
            DownloadTool(self.browser),
        ]
        playwright_server_parameters = StdioServerParameters(
            command="npx",
            args=["@playwright/mcp@latest"],
            env={"UV_PYTHON": "3.12", **os.environ}
        )
        self.mcp_client = ToolCollection.from_mcp(playwright_server_parameters)
        mcp_client = MCPClient(playwright_server_parameters)
        self.tools = mcp_client.get_tools()


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
                my_tools.GetOfficialWebsite(),
                # my_tools.verify_event_website,
                DuckDuckGoSearchTool(),
                my_tools.VerifyEvent(),
                my_tools.save_to_file
            ],
            model=self.model,
            max_steps=20,
            verbosity_level=2,
            name="URL_resolver",
            description="Validates and finds official URL",
            additional_authorized_imports=["requests", "bs4", "pandas", "os", "webbrowser", "json"],
        )
        #  result from two tools should be the same if not you have to compare result with step 2.
        agent.prompt_templates["managed_agent"][
            "task"
        ] += """You are an intelligent research agent tasked with finding the official website. Your goal is to ensure that the URL is authoritative and legitimate
        Follow these steps carefully:
        ## Plan
        ### 1. Search for the Official Website
        you can use `get_official_website` function to find official website this function will return the official website from wikipedia.
        and then you have to pic 1 website the most relevance from the search engine result most of the time the official website is listed on the first page of the search engine.
       
        ### 2. Verify the Website’s Authenticity
        you can use `verify_event_website` to verify how much score of this website you have to return only one which highest score and you think it is the official website.

        ### 3. Provide a Verified Response
        - If you confirm the official website, return the URL along with a brief justification (e.g., "This is the official website as listed on the sport’s governing body page.").
        - If no authoritative site is found, state that the information is unavailable rather than guessing.
        ##OUPUT
        Output should be in md format and
        save the output by using `save_to_file` function
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
            name="name_research_agent",
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
            name="Crawling_agent",
            description="Web crawling and analyze contents.",
        )

        agent.prompt_templates["managed_agent"][
            "task"
        ] += """
                You are a web data analyst and NLP specialist tasked with extracting **sports-related entities** from webpages and verifying their context. The goal is to identify and validate **names, teams, sponsors, and regions** from the content.

---

## TASK FLOW

### Step 1: Extract Raw Web Content
- Extract and output the **entire textual content** from the given sports-related webpage.
- Do **not truncate or summarize** the text. Preserve all structure and sections.

---

### Step 2: Identify Names and Entities
- Use context clues, known naming conventions, and databases to detect:
  - Player and rider full names
  - Team names (sponsors, pro teams)
  - Nationalities or regions
  - Coach and staff names (if available)
  - Associated sponsors
- Handle variations, nicknames, and abbreviations (e.g., "CR7" → Cristiano Ronaldo).

---

### Step 3: Cross-Check Entities
- Validate identified names by checking against:
  - Sports databases (e.g., ProCyclingStats, Transfermarkt, UCI, Wikipedia)
  - Reliable Google search queries  
    e.g. `"Danilith Nokere Koerse 2024 startlist site:procyclingstats.com"`
- Resolve ambiguity between individual names vs. team/sponsor names.

---

### Step 4: Contextual Validation
- Analyze **context around each entity**:
  - Is it a player, team, sponsor, or coach?
  - What league or race does it relate to?
  - Does the region match expected origins?

---

### Step 5: Output the Validated Entities
- Format the result in structured JSON and Markdown as follows:

### Output Format:
#### Example 1 — Just Full Names:
```json
[
  {"Full name": "Tadej Pogačar"},
  {"Full name": "Wout van Aert"},
  {"Full name": "Mads Pedersen"}
]
## ADDITIONAL RULES
- Always extract full names with correct diacritics (e.g., Søren Kragh Andersen).
- If a name or affiliation cannot be verified, write: `"Team": "[UNKNOWN]"`.
- Do not confuse geographic regions with nationality (e.g., “Flanders” ≠ “Belgium”).
- Differentiate clearly between rider names and commercial team names.
- Include UCI team names if they differ from sponsor branding.
- Output must be in clean JSON inside triple backticks.
"""
        return agent

    def agent_map(self):

        agent = CodeAgent(
            tools=[my_tools.RoadNameTool(), GoogleSearchTool()],
            model=self.model,
            # additional_authorized_imports=["json", "requests", "bs4", "pandas", "os"],
            max_steps=20,
            verbosity_level=2,
            name="Route_agent",
            description="Route and Geograpy analysis.",
        )

        agent.prompt_templates["managed_agent"][
            "task"
        ] += prompt_test.prompt9
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
            tools=[visualizer, my_tools.save_to_file],
            additional_authorized_imports=["time", "numpy", "pandas", "open", "os"],
            managed_agents=agent,
            planning_interval=3,
        )
        manager_agent.prompt_templates["managed_agent"]["task"] +=  """
        You're a meticulous analyst with a keen eye for detail. You're known for
        your ability to turn complex data into clear and concise reports, making
        it easy for others to understand and act on the information you provide.
        ## Goal
        Create detailed reports based on {topic} data analysis and research findings
        Save data in to md file use function `save_to_file`.
        ## Output
        - Use Markdown format for the report.
        - Include sections for Introduction, Methodology, Results, and Conclusion.
        """
        return manager_agent

    def run(self, task):
        # crawling = self.agent_crawling()
        url_resolve_agent = self.agent_url_validate()
        # web_agent = self.agent_web()
        name_agent = self.agent_name()
        route_agent = self.agent_map()

        manage_ag = self.manage_agent(
            [
                # name_agent,
                # crawling,
                # web_agent,
                # url_resolve_agent,
                route_agent
            ]
        )
        ans = manage_ag.run(task, max_steps=20)
        return ans

    def start(self):
        url_resolve_agent = self.agent_url_validate()
        manage_ag = self.manage_agent(
            [
                url_resolve_agent
            ]
        )
        return manage_ag

    def test_mcp(self):
        model = model_create.bedrock_model()
        playwright_server_parameters = StdioServerParameters(
            command="npx",
            args=["@playwright/mcp@latest"],
            env={"UV_PYTHON": "3.12", **os.environ}
        )
        # browser_use = StdioServerParameters(
        #     command="uvx",
        #     args=["mcp-server-browser-use"],
        #     env={"UV_PYTHON": "3.12", **os.environ}
        # )
        capcha_search = StdioServerParameters(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-puppeteer"]
        )

        with ToolCollection.from_mcp([playwright_server_parameters],
                                     trust_remote_code=True) as tool_collection:
            agent = CodeAgent(
                tools=[*tool_collection.tools],
                model=model,
                additional_authorized_imports=[
                    # "requests", "bs4", "pandas", "os",
                    "json"
                ],

            )
            agent.run(prompt_test.prompt8, max_steps=20)
if __name__ == '__main__':
    agentic = AgentM()
    # agen = agentic.start()
    # demo = GradioUI(agen)
    # demo.launch()
    agentic.run("Find the route and road name of the tour 78th Danilith Nokere Koerse list all the road name and route")
    # agentic.test_mcp()