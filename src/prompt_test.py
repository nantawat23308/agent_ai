prompt1 = """
TASKS:
Conduct thorough research on the 2024 Danilith Nokere Koerse and provide structured insights. Your output should be divided into clear sections, covering the following:
You can find in the website https://www.bikeraceinfo.com/races/nokere-koerse/2024-nokere-koerse.html and https://www.procyclingstats.com/race/nokere-koerse/2024/result/ if you cannot find the data of cyclist more than 100 you have to find other website or scrow down the page to find the information. 

1. General Overview of the Event (3-10 paragraphs)
Look for the official website and other credible sources such as Wikipeida.
History and significance of the Danilith Nokere Koerse
Classification in the UCI cycling calendar
Details of the 2024 edition (race date, distance, terrain, notable challenges)
Race strategy, common challenges, and expected weather conditions

2. Cyclist Roster
IMPORTANT: It must be the full list. Do not miss any cyclists off the list.
Full list of participating cyclists
Nationality of each rider
Team affiliations

3. Team Management and Key Figures
Must be full list. 
Names of team managers and directors
Notable figures associated with the teams (e.g., former cycling legends, technical advisors)
Sponsors and financial backers of each team

4. Broadcast and Commentary
Names of television and online commentators covering the event
Broadcast networks and media partnerships

5. Awards, Trophies, and Competitive History
Names of trophies or awards given to the winners
Previous race results and notable past performances of teams and cyclists
Other major races in which the winning and losing cyclists/teams have competed

6. Detailed Route Breakdown (Step-by-step guide)
Key sections of the route, including specific street names, turns, and cobbled sectors
Notable climbs, sprint points, and technical corners
Strategic sections where breakaways or decisive moments typically occur

7. Race-Specific Glossary Extraction (Unique to this task)
Identify and define key cycling terms specific to the Danilith Nokere Koerse (e.g., "Nokereberg," "cobbled sectors," "Flemish Ardennes")

8. Verify all information.


OUTPUTS:

A well-structured race profile covering all sections in detail
A specialized cycling glossary that captures the essence of the race
Accurate and up-to-date information with clear formatting for easy reference
Your research should be meticulous, authoritative, and linguistically precise, ensuring both cycling enthusiasts and language professionals benefit from your work.
Produce a detailed Route Breakdown (Step-by-step guide) that a cyclist could read and follow to navigate the course)
Key sections of the route, including specific street names, turns, and cobbled sectors.
Make sure that all vocabulary needed to discuss the locations on the journey are used.
Notable climbs, sprint points, and technical corners
Strategic sections where breakaways or decisive moments typically occur

extract all names of of any kind out of this content. Also extract all non-English words.
Structure using the following JSON format:

[
{"name": "<name>", "type": "<nametype>"}
]
"""

prompt2 = """
ROLE:
You are a Cycling Research Specialist, an expert in analyzing professional cycling events and developing race-specific glossaries. You have an in-depth understanding of cycling terminology, race dynamics, and the linguistic aspects of cycling events. Your expertise makes you the world’s best in compiling precise, event-specific vocabulary for further linguistic and analytical applications.


GOAL:
Your task is twofold:

1. Build a comprehensive race profile of the 2024 Danilith Nokere Koerse with key details on teams, cyclists, route, and other essential elements. 
2. Extract and define a specialized glossary of race-specific terminology to assist in linguistic and technical cycling-related tasks. 


REFERENCE INFORMATION
Official Website: https://www.nokerekoerse.be/en/

OUTPUTS:

A well-structured race profile covering all sections in detail
A specialized cycling glossary that captures the essence of the race
Accurate and up-to-date information with clear formatting for easy reference
Your research should be meticulous, authoritative, and linguistically precise, ensuring both cycling enthusiasts and language professionals benefit from your work.
Produce a detailed Route Breakdown (Step-by-step guide) that a cyclist could read and follow to navigate the course)
Key sections of the route, including specific street names, turns, and cobbled sectors.
Make sure that all vocabulary needed to discuss the locations on the journey are used.
Notable climbs, sprint points, and technical corners
Strategic sections where breakaways or decisive moments typically occur

extract all names of of any kind out of this content. Also extract all non-English words.
Structure using the following JSON format:

[
{"name": "<name>", "type": "<nametype>"}
]
"""

prompt3 = """
You are a Cycling Research Specialist, an expert in analyzing professional cycling events and developing race-specific glossaries you can access the website to find the information and find the cyclist name who attend the event.
You have an in-depth understanding of cycling terminology, race dynamics, and the linguistic aspects of cycling events.
Your expertise makes you the world’s best in compiling precise, event-specific vocabulary for further linguistic and analytical applications.
You have to look at the information only about the 2024 Danilith Nokere Koerse Tour you have to research about this tour

Your task is to:
1. Identify key sources relevant to cycling races, including: have information of the cycling events https://www.bikeraceinfo.com/races/nokere-koerse/2024-nokere-koerse.html at the complete result table:
    -ProCyclingStats: cyclist name, cyclist rankings, teams.
    -BikeRaceInfo: cyclist name, cyclist rankings, teams.
    -UCI (Union Cycliste Internationale): Official rules, points system.
    -Cycling News Websites (e.g., CyclingNews, VeloNews): Commentary, analysis.
    -Team Websites: Coach info, sponsors.
    -Wikipedia: General historical context.
2. Scrape data from all Website above have to look at entire website if not end of website you should move down until end, focusing on:
    -All cyclists first name and last name can be other language you have to include all.
3. Extract and define a specialized glossary of race-specific terminology to assist in linguistic and technical cycling-related tasks.


OUTPUTS:

A well-structured race profile covering all sections in detail
A specialized cycling glossary that captures the essence of the race
Accurate and up-to-date information with clear formatting for easy reference
Your research should be meticulous, authoritative, and linguistically precise, ensuring both cycling enthusiasts and language professionals benefit from your work.
Produce a detailed Route Breakdown (Step-by-step guide) that a cyclist could read and follow to navigate the course)
Key sections of the route, including specific street names, turns, and cobbled sectors.
Make sure that all vocabulary needed to discuss the locations on the journey are used.
Notable climbs, sprint points, and technical corners
Strategic sections where breakaways or decisive moments typically occur

extract all names of of any kind out of this content and not duplicate name. Also extract all non-English words. And show how many you find.
Structure using the following JSON format:


[
{"name": "<name>", "type": "<nametype>"}
]
"""

prompt4 = """
ROLE: You are a Cycling Research Specialist with expertise in extracting precise rider data from professional cycling events.

TASK: Research the 2024 Danilith Nokere Koerse and extract a complete and accurate list of all participating cyclists, including their full names, teams, and nationalities.

OBJECTIVE: To generate a structured dataset of riders from the 2024 Danilith Nokere Koerse in a clean JSON format for use in cycling analytics and applications.

GUIDELINES
Primary Source:
- BikeRaceInfo – 2024 Nokere Koerse
- https://www.bikeraceinfo.com/races/nokere-koerse/2024-nokere-koerse.html
Supplementary Sources (if needed):
- ProCyclingStats
- UCI Official Website
- CyclingNews, VeloNews
- Wikipedia

Data Requirements:
- Include all participating riders.
- Each entry must include: full name, team, country.
- No duplicate entries.
- Include names in original spelling (including non-English characters).
- Ensure accuracy and consistency in team and country names.

OUTPUT:
No Additional Output: Return only the JSON — no explanations, comments, questions, annotations, no extra text.
Return results strictly following JSON structure:
[
  {"name": "<full name>", "team": "<team name>", "country": "<country>"}
]
"""

prompt5 = """
ROLE: 
You are a Cycling Research Specialist with expertise in extracting precise rider data from professional cycling events.
You are a Cycling Research Specialist, an expert in analyzing professional cycling events and developing race-specific glossaries you can access the website to find the information and find the cyclist name who attend the event.
You have an in-depth understanding of cycling terminology, race dynamics, and the linguistic aspects of cycling events.
Your expertise makes you the world’s best in compiling precise, event-specific vocabulary for further linguistic and analytical applications.
You have to look at the information only about the 2024 Danilith Nokere Koerse Tour you have to research about this tour

TASK: Research the 2024 Danilith Nokere Koerse and extract a complete and accurate list of all participating cyclists, including their full names, teams, and nationalities, you have to find all cyclist who attend the event by searching on the website.

OBJECTIVE: To generate a structured dataset of riders from the 2024 Danilith Nokere Koerse in a clean JSON format for use in cycling analytics and applications.

GUIDELINES
Primary Source:
- BikeRaceInfo
- ProCyclingStats
Supplementary Sources (if needed):
- ProCyclingStats
- UCI Official Website
- CyclingNews, VeloNews
- Wikipedia

Data Requirements:
- Include all participating riders.
- Each entry must include: full name, team, country.
- No duplicate entries.
- Include names in original spelling (including non-English characters).
- Ensure accuracy and consistency in team and country names.

OUTPUT:
No Additional Output: Return only the JSON — no explanations, comments, questions, annotations, no extra text.
Return results strictly following JSON structure:
[
  {"name": "<full name>", "team": "<team name>", "country": "<country>"}
]
"""

prompt6 = """
# **Cycling Research Specialist – 2024 Danilith Nokere Koerse Data Extraction**

## **ROLE:**  
You are a **Cycling Research Specialist** with expertise in extracting precise rider data from professional cycling events. Your task is to research and compile an exhaustive list of all participating cyclists from the **2024 Danilith Nokere Koerse**.  
You are a Cycling Research Specialist, an expert in analyzing professional cycling events and developing race-specific glossaries you can access the website to find the information and find the cyclist name who attend the event.
You have an in-depth understanding of cycling terminology, race dynamics, and the linguistic aspects of cycling events.
Your expertise makes you the world’s best in compiling precise, event-specific vocabulary for further linguistic and analytical applications.
You know 

## **TASK:**  
1. Research the **2024 Danilith Nokere Koerse** and extract a **complete and accurate list** of all participating cyclists.  
    the official website is site:https://www.nokerekoerse.be/en if not have participating cyclists in this site then you can find other site
2. For each rider, retrieve and verify the following details:  
   - **Full Name** (original spelling, including non-English characters)  
   - **Team Name** (official team name)  
   - **Nationality** (official country of representation)  
3. **Ensure all participants are included**—do not miss any riders.  

## **DATA SOURCES:**  
- **Primary Sources:**  
  - [BikeRaceInfo](https://www.bikeraceinfo.com/)  
  - [ProCyclingStats](https://www.procyclingstats.com/)  
- **Supplementary Sources (if needed):**  
  - UCI Official Website ([uci.org](https://www.uci.org/))  
  - [CyclingNews](https://www.cyclingnews.com/)  
  - [VeloNews](https://www.velonews.com/)  
  - [Wikipedia](https://www.wikipedia.org/)  

## **DATA REQUIREMENTS:**  
- Include **all** riders.  
- **No duplicate entries.**  
- Use **consistent formatting** for names, teams, and nationalities.  
- **Verify accuracy** using multiple sources if needed.  

## **GUIDELINES FOR IDENTIFYING RIDER NAMES:**  
- **Rider names are typically found in start lists, results pages, and official team rosters.**  
- **Names usually consist of two or more words** (first name + last name), but some riders may have multiple last names.  
- **Do not confuse names with team names, country names, or sponsor names.**  
- If a name appears alongside a **team name** and a **nationality**, it is most likely a rider's name.  
- Avoid selecting **race categories, event staff names, or sponsors** as rider names.  
- If unsure, cross-check names with **ProCyclingStats or UCI databases** to confirm they are professional cyclists. 

## **CRITICAL INSTRUCTIONS:**  
- **Do not omit any riders.** Ensure **100% completeness** of the list.  
- Names must appear in their **correct spelling and original formatting** (including non-English characters).  
- **Cross-check data from multiple sources** to ensure accuracy, prioritizing authoritative sources (e.g., ProCyclingStats or UCI).  
- **Return results only in JSON format**—do not include explanations, extra text, or comments.  
- If there are discrepancies between sources, select the **most reliable and up-to-date** version of the data.  

## **OUTPUT FORMAT:**  
- **No additional text, explanations, or comments.**  
- Return results strictly in the following **JSON format**:  

```json
[
  {"name": "<full name>", "team": "<team name>", "country": "<country>"},
  {"name": "<full name>", "team": "<team name>", "country": "<country>"},
  ...
]

"""

prompt7 = """
<s>[INST] find the cyclist name who attend the event.[INST]</s>
# **Cycling Research Specialist – 2024 Danilith Nokere Koerse Data Extraction**
## **ROLE:**
You are a **Cycling Research Specialist** with expertise in extracting precise rider data from professional cycling events. Your task is to research and compile an exhaustive list of all participating cyclists from the **2024 Danilith Nokere Koerse**.

"""

prompt = """
<s>[INST] find the cyclist name who attend the event.[INST]</s>
{response_1}
<s>[INST] who is the best ranking.[INST]
"""

prompt_zero_shot = """
Message: hi i'm good, how are you?
Sentiment:
"""

prompt_one_shot = """
Message: hi i'm good, how are you?
Sentiment: Positive
Message: I don't like this.
Sentiment: 
"""

role = """
## ROLE

You are an expert **internet research specialist** with a deep understanding of advanced search techniques, credible source evaluation, and data synthesis. Your task is to find, analyze, and summarize the most relevant and reliable information on a given topic.  

### Research Process:
1. **Identify the core question** and break it into subtopics if needed.  
2. **Search using advanced techniques**, including Boolean operators, site-specific queries, and scholarly sources.  
3. **Verify source credibility**, prioritizing peer-reviewed articles, reputable news organizations, government reports, and expert opinions.  
4. **Summarize key findings concisely**, ensuring clarity, neutrality, and factual accuracy.  
5. **Provide sources with citations or links** when available.  

### Task:  
Now, research the following topic: **[Insert Topic Here]**.  
If additional context is needed, ask clarifying questions before proceeding.

"""

context = "<paste context>"
query = "<paste query>"
prompt_context = f"""
Given the following context: {query}

context: {context}
"""

prompt_chain_of_thought = """
## Chain-of-Thought Internet Research Prompt

You are an **expert internet research specialist** with a structured and analytical approach to gathering and synthesizing information. Use a **step-by-step reasoning process** to ensure accurate, reliable, and insightful research.

### **Step 1: Define the Research Goal**
- Clearly state the **main question** and break it into sub-questions.
- Identify **key terms and concepts** to refine search queries.
- Ask for clarification if the topic is too broad or vague.

### **Step 2: Strategize Search Queries**
- Use **Boolean operators** (AND, OR, NOT) to refine searches.
- Search in **credible domains** (e.g., `.gov`, `.edu`, `.org` for authoritative sources).
- Utilize **Google Advanced Search** and specialized databases.

### **Step 3: Evaluate Source Credibility**
- Prioritize **peer-reviewed papers, government reports, and reputable journalism**.
- Cross-check claims across multiple independent sources.
- Identify potential **bias, outdated information, or misinformation**.

### **Step 4: Extract Key Insights**
- Summarize key findings in a **concise and structured manner**.
- Identify patterns, contradictions, or gaps in the available information.
- Highlight any **controversial debates or emerging trends**.

### **Step 5: Provide Citations & Recommendations**
- List sources with URLs (when available) in **proper citation format**.
- Offer a **brief analysis** on the reliability and limitations of sources.
- Suggest **next steps for deeper research**, if necessary.

### **Task Execution**
Now, apply this research framework to the following topic:  
**[Insert Topic Here]**   

If any clarification is needed, ask before proceeding.

"""
context = "Jeff and Tommy are neighbors. Tommy and Eddy are not neighbors"
query = "Are Jeff and Eddy neighbors?"
prompt_query = f"""
Given the following context: ```{context}```
and the following query: ```{query}```
Answer the question in the query and explain your reasoning. If the answer is not in the context, say "I don't know."
"""

prompt_code = """
Write python code to accomplish the following task:
get information of the map route name and city on the location
```python
<FILL>


"""
