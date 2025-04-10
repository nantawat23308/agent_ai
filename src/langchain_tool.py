from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper



if __name__ == '__main__':

    api_wrapper = WikipediaAPIWrapper(top_k_results=1, doc_content_chars_max=100)
    tool = WikipediaQueryRun(api_wrapper=api_wrapper)
    print(tool.name)
    resp = tool.run({"query": "tour de france 2025"})
    print(resp)