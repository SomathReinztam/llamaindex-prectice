from langchain_core.embeddings.embeddings import Embeddings
from langchain_postgres.vectorstores import PGVector
from typing import List, Dict
from sqlalchemy import create_engine, text
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Clase para hacer busqueda semantica en vectors stores ya creadas
class SemanticSearchEngine:
    def __init__(self, embedding : Embeddings, connection : str, collection_name : str):
        self.embedding = embedding
        self.connection = connection
        self.collection_name = collection_name
    
        # Cargar la base de datos vectorial
        self.vector_store = PGVector.from_existing_index(
            embedding=self.embedding,
            collection_name=self.collection_name,
            connection=self.connection
        )
    
    def simple_search(self, query : str, k : int):
        """Búsqueda semántica simple"""
        results = self.vector_store.similarity_search(query, k=k)
        return results
    



# Crea una colleccion de vectores, documentos, indices en postgres 
def create_collection(embedding : Embeddings, connection : str, collection_name : str, embedding_lengt : int, text_chunks : List[str], metadatas : List[Dict] | None = None) -> List:
    vector_store = PGVector(
            embedding=embedding,
            collection_name=collection_name,
            connection=connection,
            embedding_lengt=embedding_lengt
        )

    ids = vector_store.add_texts(
        texts=text_chunks,
        metadatas=metadatas
    )
    return ids



# Ver todas las colecciones de la db
def get_all_collections(connection : str) -> List[str]:
    query = text(
    """
    select 
	    name
    from
	    langchain_pg_collection
    ;
    """
    )

    engine = create_engine(connection)
    with engine.connect() as conn:
        pks = conn.execute(query).fetchall()
    collections = [coll for coll in pks[0]]

    return collections



def doc_chunkenizer(doc_file : str, chunk_size : int = 1000, chunk_overlap : int = 200) -> List[str]:
    loader = TextLoader(doc_file, encoding="utf-8")
    docs = loader.load() # docs es una lista con Documentos de langchaing
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    splitted_docs = splitter.split_documents(docs) # Es una lista de Documentos de langchain
    chunks = [doc.page_content for doc in splitted_docs]
    return chunks


