import datasets
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.retrievers import BM25Retriever
from langchain_community.document_loaders import WebBaseLoader
import bs4
from langchain_google_vertexai import VertexAIEmbeddings
from langchain_core.vectorstores import InMemoryVectorStore
from langchain import hub
from langgraph.graph import START, StateGraph
from typing_extensions import List, TypedDict
import litellm
from langchain_aws import ChatBedrockConverse
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.chat_models import init_chat_model

class State(TypedDict):
    question: str
    context: List[Document]
    answer: str


class VecTorchRetriever:
    def __init__(self):
        # self.retriever = BM25Retriever.from_documents(docs, k=10)
        self.loader = WebBaseLoader(
            web_paths=("https://lilianweng.github.io/posts/2023-06-23-agent/",),
            bs_kwargs=dict(
                parse_only=bs4.SoupStrainer(
                    class_=("post-content", "post-title", "post-header")
                )
            ),
        )
        self.docs = self.loader.load()
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
        self.vector_store = InMemoryVectorStore(embeddings)
        self.llm = init_chat_model("meta.llama3-3-70b-instruct-v1:0", model_provider="bedrock_converse")

    @staticmethod
    def text_splitter(docs):
        text_split = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=50,
            add_start_index=True,
            strip_whitespace=True,
            separators=["\n\n", "\n", ".", " ", ""]
        )
        all_splits = text_split.split_documents(docs)
        return all_splits

    def vector_indexer(self, split_docs):
        _ = self.vector_store.add_documents(documents=split_docs)

    def retrieve(self, state: State):
        retrieved_docs = self.vector_store.similarity_search(state["question"])
        return {"context": retrieved_docs}

    def generate(self, state: State):
        prompt = hub.pull("rlm/rag-prompt")
        docs_content = "\n\n".join(doc.page_content for doc in state["context"])
        messages = prompt.invoke({"question": state["question"], "context": docs_content})
        response = self.llm.invoke(messages)
        return {"answer": response.content}


    def main(self):
        split_docs = self.text_splitter(self.docs)
        self.vector_indexer(split_docs)
        print("Number of documents:", len(split_docs))
        print("First document:", split_docs[1].page_content)
        print("First document metadata:", len(split_docs))
        graph_builder = StateGraph(State).add_sequence([self.retrieve, self.generate])
        graph_builder.add_edge(START, "retrieve")
        graph = graph_builder.compile()
        response = graph.invoke({"question": "What is Task Decomposition?"})
        print(response["answer"])


if __name__ == '__main__':
    vec_torch_retriever = VecTorchRetriever()
    vec_torch_retriever.main()