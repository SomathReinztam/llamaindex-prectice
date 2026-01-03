# from sqlalchemy import create_engine, text
# from langchain_ollama import OllamaEmbeddings
# from dotenv import load_dotenv
# import os


# load_dotenv()
# SERVER_AI_URL = os.getenv("SERVER_AI_URL")
# model = "bge-m3:latest"
# embedding = OllamaEmbeddings(model=model, base_url=SERVER_AI_URL)

# PG_CONNECTION = "postgresql+psycopg2://postgres:postgres@localhost:5432/graph_rag"

# engine = create_engine(PG_CONNECTION)

# query = "¿Nonna Lucía Le enseñó a alguien sobre restaurantes o cocina?"
# query_vec = embedding.embed_query(text=query)


# SQL_QUERY = text("""
# SELECT
#     entity_id,
#     entity_name,
#     entity_type,
#     -(entity_embedding <#> (:query_vec)::vector) AS dot_similarity
# FROM entities
# ORDER BY entity_embedding <#> (:query_vec)::vector ASC
# LIMIT 5;
# """)


# with engine.connect() as conn:
#     response = conn.execute(
#         SQL_QUERY,
#         {"query_vec": query_vec}
#     ).fetchall()


# print(response)



from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

from langchain_ollama import OllamaEmbeddings
from graph_rag.retrive import simple_entitiy_retrive_3

load_dotenv()
SERVER_AI_URL = os.getenv("SERVER_AI_URL")
embedding = OllamaEmbeddings(model="bge-m3:latest", base_url=SERVER_AI_URL)

DATABASE_URL = "postgresql+psycopg2://postgres:postgres@localhost:5432/graph_rag"
engine = create_engine(DATABASE_URL)


query = "Who is the matriarch of the Italian family?"

response = simple_entitiy_retrive_3(engine=engine, embedding=embedding, query=query, k=5)

for r in response:
    print(r)
    print("\n"*5)
