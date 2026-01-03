from typing import Tuple
from graph_rag.prompts import SYSTEM_ENTITY_RELATIONSHIP_EXTRACTION_PROMPT_1, HUMAN_ENTITY_RELATIONSHIP_EXTRACTION_PROMPT_1
from graph_rag.neo_utils import create_entity, create_relationship
from graph_rag.models import ChunkModel, EntityModel, RelationModel, CollectionModel

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.embeddings.embeddings import Embeddings
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.output_parsers import JsonOutputParser

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from neo4j import GraphDatabase

def make_graph_collection(
        file_path : str,
        chunk_size : int,
        chunk_overlap : int,
        pg_connection : str,
        neo_connection : Tuple[str, str, str],  # uri, user, password,      uri example: "bolt://localhost:7687"
        llm : BaseChatModel,
        model_embedding : Embeddings,
        collection_name : str
):
    """
    Se hace la suposicion que las tablas ChunkModel, EntityModel, RelationModel en bd de graph_rag del ususario postgres ya existen !!!!!
    Nota:

    por ahora, la primera vez que se ejecutan se deben crear manualmente la db graph_rag y ponerle la extencion vector, y ejecutar el script graph_rag/models.py para crear la tabla.

    """
    loader = TextLoader(file_path=file_path)
    docs = loader.load()
    print("Documento cargadp")

    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks = splitter.split_documents(documents=docs)
    print("Documento chunkenizado")
    print("\n")

    engine = create_engine(pg_connection)
    Session = sessionmaker(bind=engine)
    session = Session()


    collection_db = CollectionModel(
         collection_name=collection_name
    )
    session.add(collection_db)
    session.flush()


    uri, user, password = neo_connection
    driver = GraphDatabase.driver(uri=uri, auth=(user, password))

    
    id_chunk = 0
    id_entities = 0
    id_relationships = 0
    parser = JsonOutputParser()
    for j, chunk in enumerate(chunks):
        try:
            print(f"Procesando chunk {j+1}/{len(chunks)}")

            chunk_db = ChunkModel(
                chunk_id=id_chunk,
                chunk_content=chunk.page_content
            )
            session.add(chunk_db)
            print("tabla chunks procesada exitosamente")


            messages = [
                SystemMessage(content=SYSTEM_ENTITY_RELATIONSHIP_EXTRACTION_PROMPT_1),
                HumanMessage(content=HUMAN_ENTITY_RELATIONSHIP_EXTRACTION_PROMPT_1.format(text=chunk.page_content))
            ]
            ai_message = llm.invoke(messages)
            json_res = parser.parse(ai_message.content)
            print("Entidades y relaciones extraidas del chunk")


            # Conseguindo entidades
            entities_descriptios = [entity["entity_description"] for entity in json_res["entities"]]
            entities_vecs = model_embedding.embed_documents(texts=entities_descriptios)
            print("descripciones de entidades embebidas")

            entities_list = json_res["entities"]
            for i, entity in enumerate(entities_list):
                entity_db = EntityModel(
                    entity_id=id_entities,
                    entity_name=entity["entity_name"],
                    entity_type=entity["entity_type"],
                    entity_description=entity["entity_description"],
                    entity_embedding=entities_vecs[i],
                    entity_chunk_id=id_chunk
                )
                id_entities += 1
                session.add(entity_db)

    
                query = create_entity(label=entity["entity_type"])
                with driver.session() as neo_session:
                        neo_session.run(
                             query,
                             name=entity["entity_name"],
                            description=entity["entity_description"]
                        )
            print("Entidades extraidas y guardadas con exito")



            # Consiguiendo relaciones
            relations_descriptions = [relation["relationship_description"] for relation in json_res["relationships"]]
            relations_vec = model_embedding.embed_documents(texts=relations_descriptions)

            relations_list = json_res["relationships"]
            for i, relation in enumerate(relations_list):
                relation_db = RelationModel(
                     relation_id=id_relationships,
                     entity_source=relation["source_entity"],
                     entity_Target=relation["target_entity"],
                     relation_type=relation["relationship_type"],
                     relation_description=relation["relationship_description"],
                     relation_embedding=relations_vec[i],
                     relation_chunk_id=id_chunk
                )
                id_relationships += 1
                session.add(relation_db)

                query = create_relationship(rel_type=relation["relationship_type"])
                with driver.session() as neo_session:
                     neo_session.run(
                        query,
                        source=relation["source_entity"],
                        target=relation["target_entity"],
                        description=relation["relationship_description"]
                     )
            print("Relaciones extraidas y guardadas con exito")
            print("\n"*5)
            session.commit()

            id_chunk += 1
        except Exception as e:
            id_chunk += 1
            print("="*20)
            print(f"Error procesando chunk {j+1}: \n {e}\n\n\n")
            print(ai_message.content)
            print("\n\n\n")
            print("="*20)
            print("\n"*5)
        
    driver.close()
    session.close()
    print("proceso finalizado")



if __name__ == "__main__":
    from langchain_groq import ChatGroq
    from langchain_ollama import OllamaEmbeddings
    from pathlib import Path
    from dotenv import load_dotenv
    import os

    load_dotenv()

    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    model = "openai/gpt-oss-120b"
    llm = ChatGroq(model=model, temperature=0.2, api_key=GROQ_API_KEY)


    SERVER_AI_URL = os.getenv("SERVER_AI_URL")
    emb_model = "bge-m3:latest"
    embedding = OllamaEmbeddings(model=emb_model, base_url=SERVER_AI_URL)


    root = Path(__file__).resolve().parent
    file_path = root / "_docs" / "dummytext.txt"

    DATABASE_URL = "postgresql+psycopg2://postgres:postgres@localhost:5432/graph_rag"

    URI = "bolt://localhost:7687"
    USER = "neo4j"
    PASSWORD = "postgres"
    AUTH = (URI, USER, PASSWORD)

    make_graph_collection(
        file_path=file_path,
        chunk_size=4000,
        chunk_overlap=400,
        pg_connection=DATABASE_URL,
        neo_connection=AUTH,
        llm=llm,
        model_embedding=embedding
    )



