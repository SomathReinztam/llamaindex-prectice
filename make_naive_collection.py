from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.embeddings.embeddings import Embeddings
from langchain_postgres.vectorstores import PGVector


def make_naive_collection(
        collection_name : str,
        file_path : str, 
        chunk_size : int, 
        chunk_overlap : int, 
        model_embedding : Embeddings, 
        connection : str,
        embedding_length : int,
)->list[str]:
    """
    Esta funcion se encarga de cargar un archivo .txt, chunkenizarlo, indexarlo y guardarlo en un db postgres
    """
    loader = TextLoader(file_path=file_path)
    docs = loader.load() 

    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks = splitter.split_documents(documents=docs)

    vector_store = PGVector(
        embeddings=model_embedding,
        connection=connection,
        embedding_length=embedding_length,
        collection_name=collection_name
    )

    ids = vector_store.add_documents(documents=chunks)

    return ids



if __name__ == "__main__":
    from langchain_ollama import OllamaEmbeddings
    from dotenv import load_dotenv
    from pathlib import Path
    import os

    root = Path(__file__).resolve().parent
    file_path = root / "_docs" / "texts" / "dummytext.txt"

    load_dotenv()
    SERVER_AI_URL = os.getenv("SERVER_AI_URL")
    model = "bge-m3:latest"
    embeddings_model = OllamaEmbeddings(model=model, base_url=SERVER_AI_URL)

    NAIVE_RAG_CONNECTION = os.getenv("NAIVE_RAG_CONNECTION")

    make_naive_collection(
        collection_name="Amicos Family",
        file_path=file_path,
        chunk_size=4000,
        chunk_overlap=400,
        connection=NAIVE_RAG_CONNECTION,
        embedding_length=1024
    )



