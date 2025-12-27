from typing import List
from langchain_core.documents import Document
from langchain_core.embeddings.embeddings import Embeddings
from sqlalchemy.engine.base import Engine
from langchain_core.language_models.chat_models import BaseChatModel
from neo4j._sync.driver import Driver

from sqlalchemy.orm import sessionmaker
from utils_pg.models import ChunkModel, EntityModel, RelationModel
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import JsonOutputParser

from prompts.graphRag import SYSTEM_ENTITY_RELATIONSHIP_EXTRACTION_PROMPT_1, HUMAN_ENTITY_RELATIONSHIP_EXTRACTION_PROMPT_1
from utils_neo4j.graph import create_entity, create_relationship


def make_index(chunks : List[Document], model_embedding : Embeddings, engine : Engine, llm : BaseChatModel, driver : Driver):
    """
    Aquí se asume que la las tablas ChunkModel, EntityModel, RelationModel de la base de datos ya estan creadas.

    Cosas a mejorar:
    - funciones de neo4j deben ser mas robustas, leer utils_neo4j/README.md
    - En postgres las tablas de entidades y relaciones no se está creando la columna del chunk del indice; agrafrala manualmente.
    - Para lo anterior, crear las columnas de indice manuelamente.
    """
    print(f"iniciando seccion")
    Session = sessionmaker(bind=engine)
    session = Session()

    parser = JsonOutputParser()
    print(f"procesando {len(chunks)}")
    for j, chunk in enumerate(chunks):
        try:
            print(f"Procesando Chunk {j+1}/{len(chunks)}")

            print("registrando relación chunk")
            chunk_text = chunk.page_content
            chunk_vec = model_embedding.embed_query(text=chunk_text)

            chunk_db = ChunkModel(
                chunk_content=chunk_text,
                chunk_embedding=chunk_vec
            )

            session.add(chunk_db)
            session.flush() # Esto genera el chunk_id automáticamente
            print("fin registro relacion chunk")

            human_message = HumanMessage(content=HUMAN_ENTITY_RELATIONSHIP_EXTRACTION_PROMPT_1.format(text=chunk_text))
            messages = [
                SystemMessage(content=SYSTEM_ENTITY_RELATIONSHIP_EXTRACTION_PROMPT_1),
                human_message
            ]

            
            ai_message = llm.invoke(messages)
            json_res = parser.parse(ai_message.content)
            print("entidades y relaciones extraidas")

            
            entities_descriptios = [entity["entity_description"] for entity in json_res["entities"]]
            entities_vecs = model_embedding.embed_documents(texts=entities_descriptios)
            print("descripciones de entidades embebidas")

            entities_list = json_res["entities"]
            for i, entity in enumerate(entities_list):
                entity_db = EntityModel(
                    entity_name=entity["entity_name"],
                    entity_type=entity["entity_type"],
                    entity_description=entity["entity_description"],
                    entity_embedding=entities_vecs[i]
                )
                session.add(entity_db)

                with driver.session() as neo_session:
                    neo_session.run(
                        create_entity(
                            name=entity["entity_name"],
                            label=entity["entity_type"],
                            description=entity["entity_description"]
                        )
                    )
            print("entidades guardadas en las dbs")

            relations_descriptions = [relation["relationship_description"] for relation in json_res["relationships"]]
            relations_vec = model_embedding.embed_documents(texts=relations_descriptions)

            relations_list = json_res["relationships"]
            for i, relation in enumerate(relations_list):
                relation_db = RelationModel(
                    relation_type=relation["relationship_type"],
                    relation_description=relation["relationship_description"],
                    relation_embedding=relations_vec[i]
                )
                session.add(relation_db)

                with driver.session() as neo_session:
                    neo_session.run(
                        create_relationship(
                            source=relation["source_entity"],
                        target=relation["target_entity"],
                        rel_type=relation["relationship_type"],
                        description=relation["relationship_description"]
                        )
                    )
            print("relaciones guardadas en las dbs")
            print("\n"*5)
            session.commit()
        except Exception as e:
            print("==============================")
            print(f"error en chunk {j}:\n\n {e} \n")
            print("==============================")
            print("\n"*5)
       
    driver.close()
    session.close()
    print("proceso finalizado")


        

if __name__ == "__main__":
    from pathlib import Path
    from langchain_community.document_loaders import TextLoader
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    from langchain_ollama import OllamaEmbeddings
    from dotenv import load_dotenv
    import os

    from sqlalchemy import create_engine

    from langchain_groq import ChatGroq

    from neo4j import GraphDatabase

    load_dotenv()

    root = Path(__file__).resolve().parent
    doc_file = root / "_docs" / "dummytext.txt"

    loader = TextLoader(file_path=doc_file)
    docs = loader.load()

    chunkenizer = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200)
    chunks = chunkenizer.split_documents(docs)

    # -----------
    
    SERVER_AI_URL = os.getenv("SERVER_AI_URL")
    model="bge-m3:latest"
    model_embedding = OllamaEmbeddings(model=model, base_url=SERVER_AI_URL)

    # -----------

    DATABASE_URL = "postgresql+psycopg2://langchain:langchain@localhost:5432/langchain"
    engine = create_engine(DATABASE_URL)

    # -----------

    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    model = "openai/gpt-oss-120b"
    llm = ChatGroq(model=model, temperature=0.3, api_key=GROQ_API_KEY)

    # -----------

    URI = "bolt://localhost:7687"
    USER = "neo4j"
    PASSWORD = "langchain"
    AUTH = (USER, PASSWORD)
    driver = GraphDatabase.driver(URI, auth=AUTH)

    # -----------
    # -----------

    make_index(
        chunks=chunks,
        model_embedding=model_embedding,
        engine=engine,
        llm=llm,
        driver=driver
    )


    
    


