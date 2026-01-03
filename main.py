from sqlalchemy import text, create_engine
from NEO_make_graph_collection import make_graph_collection

from langchain_core.embeddings.embeddings import Embeddings
from langchain_core.language_models.chat_models import BaseChatModel

from neo4j import GraphDatabase
import networkx as nx
from pyvis.network import Network
import webbrowser  
import os

from typing import Tuple

class GraphRetrive:
    def __init__(self):
        pass
    
    # devuelve una lista de el nombre de todas las colecciones en la base de datos
    def all_collections(self, pg_connection : str):
        engine = create_engine(pg_connection)
        query = text("""
                    SELECT collection_name
                    FROM collections;
            """)
        with engine.connect() as conn:
            response = conn.execute(query).fetchall()
        if len(response) == 0:
            return response
        return [x[0] for x in response]
    
    # Esta funcion se encarga de llenar la base de datos con los vectores y demas informacion de las entidades y relaciones y construlle el grafo en neo4j
    def make_collection(
            self,
            file_path : str,
            chunk_size : int,
            chunk_overlap : int,
            pg_connection : str,
            neo_connection : Tuple[str, str, str],  # uri, user, password,      uri example: "bolt://localhost:7687"
            llm : BaseChatModel,
            model_embedding : Embeddings,
            collection_name : str
    ):
        all_collections = self.all_collections(pg_connection=pg_connection)
        if collection_name in all_collections:
            print("Esta coleccion ya existe")
            return
        print(f"creando nueva coleccion: {collection_name}")
        make_graph_collection(file_path, chunk_size, chunk_overlap, pg_connection, neo_connection, llm, model_embedding, collection_name)

    
    def make_simple_entity_retrive(self, query : str, k : int, embedding : Embeddings, pg_connection : str):
        query_vec = embedding.embed_query(text=query)
        engine = create_engine(pg_connection)
        ENTITY_QUERY = text("""
            SELECT
                c.chunk_id,
                c.chunk_content AS text,
                MAX(-(e.entity_embedding <#> (:query_vec)::vector)) AS dot_similarity
            FROM chunks c
            JOIN entities e
                ON c.chunk_id = e.entity_chunk_id
            GROUP BY c.chunk_id, c.chunk_content
            ORDER BY dot_similarity DESC
            LIMIT :k;
        """)

        with engine.connect() as conn:
            response = conn.execute(
                ENTITY_QUERY,
                {"k":k, "query_vec":query_vec}
            ).fetchall()
        return response
    

    def make_simple_relationship_retrive(self, query : str, k : int, embedding : Embeddings, pg_connection : str):
        query_vec = embedding.embed_query(text=query)
        engine = create_engine(pg_connection)
        RELATIONSHIP_QUERY = text("""
            SELECT
                c.chunk_id,
                c.chunk_content AS text,
                MAX(-(r.relation_embedding <#> (:query_vec)::vector)) AS dot_similarity
            FROM chunks c
            JOIN relationships r
                ON c.chunk_id = r.relation_chunk_id
            GROUP BY c.chunk_id, c.chunk_content
            ORDER BY dot_similarity DESC
            LIMIT :k;
        """)

        with engine.connect() as conn:
            response = conn.execute(
                RELATIONSHIP_QUERY,
                {"k":k, "query_vec":query_vec}
            ).fetchall()
        return response
        

        
    def show_retrive(self, top_entity : int, top_relationship : int, embedding : Embeddings, pg_connection : str):
        while True:
            print("\n\n")
            human_message = input()
            query = human_message
            if human_message in ["exit"]:
                return
            print("================================== Human Query ==================================")
            print(human_message)
            print("\n")
            print("================================== Busqueda Semantica Identidades ==================================")
            entitiy_rows = self.make_simple_entity_retrive(query=query, k=top_entity, embedding=embedding, pg_connection=pg_connection)
            for row in entitiy_rows:
                tex = row[1]
                print(tex)
                print("\n\n")
            print("================================== Busqueda Semantica Relaciones ==================================")
            relation_rows = self.make_simple_relationship_retrive(query=query, k=top_relationship, embedding=embedding, pg_connection=pg_connection)
            for row in relation_rows:
                tex = row[1]
                print(tex)
                print("\n\n")
    



    def show_graph(self, uri, user, password):
        driver = GraphDatabase.driver(uri, auth=(user, password))
        G = nx.DiGraph()

        query = """
        MATCH (n)-[r]->(m)
        RETURN n, r, m
        """

        with driver.session() as session:
            result = session.run(query)

            for record in result:
                n = record["n"]
                m = record["m"]
                r = record["r"]

                # Usar element_id en lugar de id
                n_id = n.element_id
                m_id = m.element_id
                
                G.add_node(n_id, label=list(n.labels)[0] if n.labels else "Node", **dict(n))
                G.add_node(m_id, label=list(m.labels)[0] if m.labels else "Node", **dict(m))
                G.add_edge(n_id, m_id, label=r.type)

        driver.close()
        
        # Configurar pyvis para mejor visualización
        net = Network(
            notebook=False,  # Cambiar a False si no estás en Jupyter
            directed=True,
            height="750px",
            width="100%",
            bgcolor="#ffffff",
            font_color="black"
        )
        
        # Personalizar opciones de visualización
        net.set_options("""
        var options = {
        "nodes": {
            "font": {
            "size": 14
            }
        },
        "edges": {
            "arrows": {
            "to": {
                "enabled": true,
                "scaleFactor": 0.5
            }
            },
            "font": {
            "size": 12
            }
        },
        "physics": {
            "enabled": true
        }
        }
        """)
        
        net.from_nx(G)

        output_file = "neo4j_graph.html"
        net.save_graph(output_file)
        
        # Ruta absoluta del archivo
        abs_path = os.path.abspath(output_file)
        print(f"Grafo generado exitosamente: {abs_path}")
        
        # Abrir automáticamente en el navegador
        webbrowser.open(f'file://{abs_path}')

        # Se crea el archivo: neo4j_graph.html
        # En Linux:
        # xdg-open neo4j_graph.html
                
        

    

if __name__ == "__main__":
   
    from pathlib import Path
    from dotenv import load_dotenv
    import os
    from langchain_ollama import OllamaEmbeddings
    from langchain_groq import ChatGroq

    root = Path(__file__).resolve().parent
    file_path = root / "_docs" / "dummytext.txt"
    collection_name = file_path.stem

    load_dotenv()
    SERVER_AI_URL = os.getenv("SERVER_AI_URL")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")


    emb_model = "bge-m3:latest"
    embedding = OllamaEmbeddings(model=emb_model, base_url=SERVER_AI_URL)

    chat_model = "openai/gpt-oss-120b"
    llm = ChatGroq(model=chat_model, temperature=0.2, api_key=GROQ_API_KEY)

    CONN = "postgresql+psycopg2://postgres:postgres@localhost:5432/graph_rag"

    URI = "bolt://localhost:7687"
    USER = "neo4j"
    PASSWORD = "postgres"


    # graph_rag = GraphRetrive()

    # # Indexamos el documento si no lo está y construimos el grafo de identidades y relaciones en neo4j
    # graph_rag.make_collection(
    #     file_path=file_path,
    #     chunk_size=3000,
    #     chunk_overlap=300,
    #     pg_connection=CONN,
    #     neo_connection=(URI, USER, PASSWORD),
    #     llm=llm,
    #     model_embedding=embedding,
    #     collection_name=collection_name
    # )

    # # hacemos retrive
    # graph_rag.show_retrive(top_entity=2, top_relationship=2, embedding=embedding, pg_connection=CONN)

    # # Hacemos una gráfica del grafo de relaciones, esto hace un archivo .html y una carpeta lib con código javascript
    # graph_rag.show_graph(uri=URI, user=USER, password=PASSWORD)

    grap_rag = GraphRetrive()
    r = grap_rag.all_collections(pg_connection=CONN)
    print(r)

