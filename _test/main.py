from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import JsonOutputParser

from prompts import SYSTEM_ENTITY_RELATIONSHIP_EXTRACTION_PROMPT_1, HUMAN_ENTITY_RELATIONSHIP_EXTRACTION_PROMPT_1
from pathlib import Path
from dotenv import load_dotenv
import os
from neo4j import GraphDatabase
from sqlalchemy import text, create_engine





# ================== 
root = Path(__file__).resolve().parent.parent
book_file = root / "_docs" / "book.txt"

text_loader = TextLoader(file_path=book_file)

docs = text_loader.load()
n_idx = len(docs)

chunkenizer = RecursiveCharacterTextSplitter(chunk_size=3000, chunk_overlap=600)
chunks = chunkenizer.split_documents(docs) # Lista en donde cada elemento es un Documento de langchain
# ================== 


# ================== 
load_dotenv()

SERVER_AI_URL = os.getenv("SERVER_AI_URL")
model = "bge-m3:latest"
embedding = OllamaEmbeddings(model=model, base_url=SERVER_AI_URL)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
model = "openai/gpt-oss-120b"
llm = ChatGroq(model=model, temperature=0.3, api_key=GROQ_API_KEY)

parser = JsonOutputParser()




# ================== 

chunk_id = [] # Columna primaria
chunk_content = []
embedding_chunk = [] # almacena los vectores

entity_id = [] # Columna primaria
entity_name = []
entity_type = []
entity_description = []
entity_embedding = []
entity_chunk_id = []

relation_id = [] # Columna primaria
relation_type = []
relation_description = []
relation_embedding = []
relation_chunk_id = []


# ======================


def create_entity(name, label, description):
    query = """
MERGE (e:{label} {{name: '{name}'}})
SET e.description = '{description}'
    """
    return query.format(name=name, label=label, description=description)

def create_relationship(source, target, rel_type, description):
    query = """
MATCH (a {{name: '{source}'}})
MATCH (b {{name: '{target}'}})
MERGE (a)-[r:{rel_type}]->(b)
SET r.description = '{description}'
    """
    return query.format(source=source, target=target, rel_type=rel_type, description=description)


URI = "bolt://localhost:7687"
USER = "neo4j"
PASSWORD = "langchain"
AUTH = (USER, PASSWORD)

driver = GraphDatabase.driver(URI, auth=AUTH)

# ======================




chunk_idx = 0
entity_idx = 0
relation_idx = 0
for chunk in chunks:
    chunk_content.append(chunk_idx)
    chunk_content.append(chunk.page_content)
    embedding_chunk.append(embedding.embed_query(text=chunk))

    humam_message = HUMAN_ENTITY_RELATIONSHIP_EXTRACTION_PROMPT_1.format(text=chunk.page_content)
    messages = [
        SystemMessage(content=SYSTEM_ENTITY_RELATIONSHIP_EXTRACTION_PROMPT_1),
        HumanMessage(content=humam_message)
    ]
    ai_message = llm.invoke(messages)
    json = parser.parse(ai_message.content)


    for n in range(len(json["entities"])):
        entity_chunk_id.append(chunk_idx)
        entity_id.append(entity_idx)
        entity_idx += 1

        entity = json["entities"][n]

        entity_name.append(entity["entity_name"])
        entity_type.append(entity["entity_type"])
        entity_description.append(entity["entity_description"])

    entity_chunk_descriptions = [entity["entity_description"] for entity in json["entities"]]
    entity_chunk_embeddings = embedding.embed_documents(texts=entity_chunk_descriptions)

    entity_embedding += entity_chunk_embeddings



    for n in range(len(json["relationships"])):
        relation_chunk_id.append(chunk_idx)
        relation_id.append(relation_idx)
        relation_idx += 1

        relation = json["relationships"][n]
        relation_type.append(relation["relationship_type"])
        relation_description.append(relation["relationship_description"])
    
    relation_chunk_descriptions = [relation["relationships"] for relation in json["relationships"]]
    relation_chunk_embedding = embedding.embed_documents(texts=relation_chunk_descriptions)
    relation_embedding += relation_chunk_embedding

    chunk_idx += 1



    with driver.session() as session:
        for entity in json["entities"]:
            session.run(
                create_entity(
                    name=entity["entity_name"],
                    label=entity["entity_type"],
                    description=entity["entity_description"]
                )
            )
        
        for rel in json["relationships"]:
            session.run(
                create_relationship(
                    source=rel["source_entity"],
                    target=rel["target_entity"],
                    rel_type=rel["relationship_type"],
                    description=rel["relationship_description"]
                )
            )
    
    driver.close()
