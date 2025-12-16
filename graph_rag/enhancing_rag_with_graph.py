from langchain_neo4j.graphs.neo4j_graph  import Neo4jGraph
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_neo4j.vectorstores.neo4j_vector import Neo4jVector

from dotenv import load_dotenv
from pathlib import Path
import os

root = Path(__file__)
file_path = root / "_docs" / "dummytext.txt"

load_dotenv()
SERVER_AI_URL = os.getenv("SERVER_AI_URL")

graph = Neo4jGraph()

loader = TextLoader(file_path=file_path)
docs = loader.load()

text_splitter = RecursiveCharacterTextSplitter(chunk_size=250, chunk_overlap=24)
documents = text_splitter.split_documents(documents=docs)

model = "gpt-oss:20b"
llm = ChatOllama(model=model, temperature=0.2, base_url=SERVER_AI_URL)
llm_transformer = LLMGraphTransformer(llm=llm)
graph_documents = llm_transformer.convert_to_graph_documents(documents)

graph_documents[0]


graph.add_graph_documents(
    graph_documents,
    baseEntityLabel=True,
    include_source=True
)


model_emb = "bge-m3:latest"
embeddings = OllamaEmbeddings(model=model_emb, base_url=SERVER_AI_URL)

vector_index = Neo4jVector.from_existing_graph(
    embeddings,
    search_type="hybrid",
    node_label="Document",
    text_node_properties=["text"],
    embedding_node_property="embedding"
)
vector_retriever = vector_index.as_retriever()


