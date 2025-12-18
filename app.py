import streamlit as st
import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_ollama import OllamaEmbeddings

# Importaciones de tu script original
from utils.semantic_search import get_all_collections, doc_chunkenizer, create_collection, SemanticSearchEngine

# Configuración de página
st.set_page_config(page_title="Semantic Search Engine", layout="wide")

# Cargar variables de entorno
load_dotenv()
CONNECTION = os.getenv("CONNECTION")
SERVER_AI_URL = os.getenv("SERVER_AI_URL")

# --- Funciones de Cache para optimizar ---
@st.cache_resource
def get_embeddings_model():
    model = "bge-m3:latest"
    return OllamaEmbeddings(model=model, base_url=SERVER_AI_URL)

def refresh_collections():
    return get_all_collections(connection=CONNECTION)

# --- Lógica de la App ---
def main():
    st.title("🔎 Postgres Vector Search")
    
    # 1. Inicializar Embeddings
    embeddings_model = get_embeddings_model()
    embedding_length = 1024

    # 2. Barra Lateral: Gestión de Colecciones
    st.sidebar.header("Gestión de Colecciones")
    
    # Listar colecciones actuales
    try:
        collections = refresh_collections()
    except Exception as e:
        st.error(f"Error conectando a la DB: {e}")
        return

    selected_collection = st.sidebar.selectbox("Selecciona una colección", collections)

    st.sidebar.divider()
    
    # Subir nuevo archivo
    st.sidebar.subheader("Indexar nuevo archivo")
    uploaded_file = st.sidebar.file_uploader("Subir archivo .txt", type=["txt"])
    
    if uploaded_file is not None:
        collection_name = Path(uploaded_file.name).stem
        
        if st.sidebar.button(f"Indexar {collection_name}"):
            if collection_name in collections:
                st.sidebar.warning("La colección ya existe.")
            else:
                with st.spinner("Procesando e indexando..."):
                    # Guardar temporalmente para usar tu función doc_chunkenizer
                    temp_path = Path(f"temp_{uploaded_file.name}")
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    try:
                        # Tu lógica original
                        chunks = doc_chunkenizer(doc_file=str(temp_path))
                        ids = create_collection(
                            embedding=embeddings_model, 
                            connection=CONNECTION, 
                            collection_name=collection_name, 
                            embedding_lengt=embedding_length, 
                            text_chunks=chunks
                        )
                        st.sidebar.success(f"¡Éxito! {len(ids)} chunks indexados.")
                        st.rerun() # Refrescar para que aparezca en el selectbox
                    except Exception as e:
                        st.error(f"Error: {e}")
                    finally:
                        if temp_path.exists():
                            os.remove(temp_path)

    # 3. Panel Principal: Búsqueda
    if selected_collection:
        st.header(f"Colección actual: `{selected_collection}`")
        
        # Inicializar el motor de búsqueda
        engine = SemanticSearchEngine(
            embedding=embeddings_model, 
            connection=CONNECTION, 
            collection_name=selected_collection
        )

        query = st.text_input("Haz una pregunta sobre los documentos:", placeholder="Ej. ¿De qué trata el texto?")

        if query:
            with st.spinner("Buscando coincidencias..."):
                results = engine.simple_search(query=query, k=5)
                
                if not results:
                    st.info("No se encontraron resultados relevantes.")
                
                for i, doc in enumerate(results, 1):
                    with st.container():
                        st.markdown(f"### Resultado {i}")
                        st.write(doc.page_content)
                        
                        # Mostrar metadatos en un pequeño expander
                        with st.expander("Ver Metadatos"):
                            st.json(doc.metadata)
                        st.divider()
    else:
        st.info("👈 Selecciona o sube una colección en la barra lateral para comenzar.")

if __name__ == "__main__":
    main()