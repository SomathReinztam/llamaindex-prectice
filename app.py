import streamlit as st
import streamlit.components.v1 as components
from sqlalchemy import text, create_engine
from langchain_core.embeddings.embeddings import Embeddings
from langchain_core.language_models.chat_models import BaseChatModel
from neo4j import GraphDatabase
import networkx as nx
from pyvis.network import Network
import os
from typing import Tuple
from pathlib import Path
from dotenv import load_dotenv

# Importaciones externas (asegurate de que este archivo exista en tu directorio)
try:
    from NEO_make_graph_collection import make_graph_collection
except ImportError:
    st.error("No se encontró el módulo 'NEO_make_graph_collection'. Asegúrate de que el archivo esté en el mismo directorio.")

# --- Configuración de la Página ---
st.set_page_config(page_title="GraphRAG Explorer", layout="wide", page_icon="🕸️")

# --- Clase Refactorizada para Streamlit ---
class GraphRetrive:
    def __init__(self):
        pass
    
    def all_collections(self, pg_connection : str):
        try:
            engine = create_engine(pg_connection)
            query = text("SELECT collection_name FROM collections;")
            with engine.connect() as conn:
                response = conn.execute(query).fetchall()
            return [row[0] for row in response] # Retornar lista limpia
        except Exception as e:
            st.error(f"Error conectando a Postgres: {e}")
            return []
    
    def make_collection(
            self,
            file_path : str,
            chunk_size : int,
            chunk_overlap : int,
            pg_connection : str,
            neo_connection : Tuple[str, str, str],
            llm : BaseChatModel,
            model_embedding : Embeddings,
            collection_name : str
    ):
        all_cols = self.all_collections(pg_connection=pg_connection)
        if collection_name in all_cols:
            st.warning(f"La colección '{collection_name}' ya existe. Usando la existente.")
            return False
        
        with st.spinner(f"Creando colección: {collection_name}... Esto puede tardar."):
            try:
                # Llamada a tu funcion externa
                make_graph_collection(file_path, chunk_size, chunk_overlap, pg_connection, neo_connection, llm, model_embedding, collection_name)
                st.success(f"Colección '{collection_name}' creada exitosamente.")
                return True
            except Exception as e:
                st.error(f"Error al crear la colección: {e}")
                return False

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
            response = conn.execute(ENTITY_QUERY, {"k":k, "query_vec":query_vec}).fetchall()
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
            response = conn.execute(RELATIONSHIP_QUERY, {"k":k, "query_vec":query_vec}).fetchall()
        return response

    def generate_graph_html(self, uri, user, password, output_file="neo4j_graph.html"):
        """Genera el HTML del grafo y retorna la ruta."""
        try:
            driver = GraphDatabase.driver(uri, auth=(user, password))
            G = nx.DiGraph()

            # Limitamos la consulta para evitar colapsar el navegador si hay demasiados nodos
            query = """
            MATCH (n)-[r]->(m)
            RETURN n, r, m
            LIMIT 300 
            """

            with driver.session() as session:
                result = session.run(query)
                for record in result:
                    n = record["n"]
                    m = record["m"]
                    r = record["r"]
                    
                    n_id = n.element_id
                    m_id = m.element_id
                    
                    # Etiquetas y propiedades para el tooltip
                    n_label = list(n.labels)[0] if n.labels else "Node"
                    m_label = list(m.labels)[0] if m.labels else "Node"
                    
                    G.add_node(n_id, label=n_label, title=str(dict(n)), group=n_label)
                    G.add_node(m_id, label=m_label, title=str(dict(m)), group=m_label)
                    G.add_edge(n_id, m_id, label=r.type, title=r.type)

            driver.close()
            
            if G.number_of_nodes() == 0:
                st.warning("No se encontraron nodos ni relaciones en la base de datos Neo4j.")
                return None

            # Configurar Pyvis
            net = Network(height="750px", width="100%", bgcolor="#ffffff", font_color="black", directed=True)
            
            # Opciones de física y layout
            net.set_options("""
            var options = {
                "nodes": { "font": { "size": 14 } },
                "edges": { "arrows": { "to": { "enabled": true, "scaleFactor": 0.5 } }, "smooth": { "type": "continuous" } },
                "physics": { "stabilization": false, "barnesHut": { "gravitationalConstant": -8000, "springConstant": 0.04, "springLength": 95 } }
            }
            """)
            
            net.from_nx(G)
            net.save_graph(output_file)
            return output_file
        except Exception as e:
            st.error(f"Error generando el grafo: {e}")
            return None

# --- Inicialización de Modelos y Variables (Cached) ---
@st.cache_resource
def load_models():
    load_dotenv()
    SERVER_AI_URL = os.getenv("SERVER_AI_URL")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    
    # Importaciones dentro para evitar errores si no se ejecutan
    from langchain_ollama import OllamaEmbeddings
    from langchain_groq import ChatGroq

    emb_model = "bge-m3:latest"
    embedding = OllamaEmbeddings(model=emb_model, base_url=SERVER_AI_URL)

    chat_model = "openai/gpt-oss-120b" # Ajusta según tu modelo en Groq
    llm = ChatGroq(model=chat_model, temperature=0.2, api_key=GROQ_API_KEY)
    
    return embedding, llm

# --- Interfaz de Usuario ---

# Sidebar para Configuración
with st.sidebar:
    st.header("⚙️ Configuración")
    
    st.subheader("Base de Datos Postgres")
    pg_conn_str = st.text_input("Postgres Connection", value="postgresql+psycopg2://postgres:postgres@localhost:5432/graph_rag", type="password")
    
    st.subheader("Neo4j")
    neo_uri = st.text_input("URI", value="bolt://localhost:7687")
    neo_user = st.text_input("User", value="neo4j")
    neo_pass = st.text_input("Password", value="postgres", type="password")

    # Botón de recarga de modelos (opcional)
    if st.button("Recargar Modelos"):
        st.cache_resource.clear()
        st.success("Caché limpiada.")

try:
    embedding_model, llm_model = load_models()
    graph_rag = GraphRetrive()
except Exception as e:
    st.error(f"Error cargando modelos o variables de entorno: {e}")
    st.stop()

st.title("🕸️ GraphRAG: Indexación y Búsqueda")

# Pestañas principales
tab1, tab2, tab3 = st.tabs(["📁 Cargar Datos", "🔍 Búsqueda", "📊 Grafo"])

# --- TAB 1: Cargar y Procesar Datos ---
with tab1:
    st.subheader("Subir Archivo .txt")
    uploaded_file = st.file_uploader("Elige un archivo de texto", type="txt")
    
    if uploaded_file is not None:
        # Guardar archivo temporalmente
        temp_dir = Path("temp_docs")
        temp_dir.mkdir(exist_ok=True)
        file_path = temp_dir / uploaded_file.name
        
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        st.info(f"Archivo cargado: {uploaded_file.name}")
        
        collection_name_input = st.text_input("Nombre de la Colección", value=file_path.stem)
        
        if st.button("🚀 Indexar y Crear Grafo"):
            graph_rag.make_collection(
                file_path=file_path,
                chunk_size=8000,
                chunk_overlap=2000,
                pg_connection=pg_conn_str,
                neo_connection=(neo_uri, neo_user, neo_pass),
                llm=llm_model,
                model_embedding=embedding_model,
                collection_name=collection_name_input
            )

# --- TAB 2: Búsqueda (Retrieval) ---
with tab2:
    st.subheader("Consultar la Base de Conocimiento")
    
    query = st.text_input("Escribe tu pregunta aquí:")
    
    col1, col2 = st.columns(2)
    with col1:
        top_k_ent = st.number_input("Top Entidades", min_value=1, value=2)
    with col2:
        top_k_rel = st.number_input("Top Relaciones", min_value=1, value=2)

    if st.button("🔎 Buscar"):
        if not query:
            st.warning("Por favor escribe una query.")
        else:
            with st.spinner("Buscando vectores..."):
                st.markdown("### 🧩 Entidades Relevantes")
                entity_rows = graph_rag.make_simple_entity_retrive(query, top_k_ent, embedding_model, pg_conn_str)
                if entity_rows:
                    for i, row in enumerate(entity_rows):
                        with st.expander(f"Resultado Entidad #{i+1} (Score: {row[2]:.4f})"):
                            st.write(row[1])
                else:
                    st.write("No se encontraron entidades.")

                st.markdown("### 🔗 Relaciones Relevantes")
                rel_rows = graph_rag.make_simple_relationship_retrive(query, top_k_rel, embedding_model, pg_conn_str)
                if rel_rows:
                    for i, row in enumerate(rel_rows):
                        with st.expander(f"Resultado Relación #{i+1} (Score: {row[2]:.4f})"):
                            st.write(row[1])
                else:
                    st.write("No se encontraron relaciones.")

# --- TAB 3: Visualización del Grafo ---
with tab3:
    st.subheader("Visualización en Neo4j")
    st.markdown("Visualiza las relaciones creadas en la base de datos.")
    
    if st.button("🎨 Generar/Actualizar Grafo"):
        with st.spinner("Generando visualización..."):
            html_file = graph_rag.generate_graph_html(neo_uri, neo_user, neo_pass)
            
            if html_file and os.path.exists(html_file):
                # Leer el archivo HTML y renderizarlo
                with open(html_file, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                
                # Renderizar en Streamlit
                components.html(html_content, height=800, scrolling=True)
                
                st.success(f"Grafo renderizado desde {html_file}")
            else:
                st.error("No se pudo cargar el archivo HTML del grafo.")