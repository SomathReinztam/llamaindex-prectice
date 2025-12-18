from utils.semantic_search import get_all_collections, doc_chunkenizer, create_collection, SemanticSearchEngine
from langchain_core.embeddings.embeddings import Embeddings
from pathlib import Path

from dotenv import load_dotenv
import os
load_dotenv()
CONNECTION = os.getenv("CONNECTION")


def main_(collection_file : str, embedding : Embeddings, embedding_lengt : int):
    # collection_file es un archivo por ahora .txt que se tiene indexado en un vectos store y si no lo está se indexa
    collection_name = Path(collection_file).stem
    
    # Conseguir el nombre de todas las colecciones de almacenes de vectores guardadas en la db de postgres
    collections = get_all_collections(connection=CONNECTION)
    print(f"Colleciones conseguidas:\n {collections}")

    # Si la coleccion no está en la bd se procede a cunkenizar e index el archivo .txt a la bd
    if not (collection_name in collections):
        print("la collecion no está en la db. Se procede a indexarla")
        chunks = doc_chunkenizer(doc_file=collection_file)
        print("funckenizacion exitosa")
        ids = create_collection(embedding=embedding, connection=CONNECTION, collection_name=collection_name, embedding_lengt=embedding_lengt, text_chunks=chunks)
        print(f"indexacion exitosa. Primeros 5 indices {ids[:5]}")

    PG_vector = SemanticSearchEngine(embedding=embedding, connection=CONNECTION, collection_name=collection_name)
    print("Base de datos sicronizada con la colleccion")
    print("\n"*5)

    while True:
        print("\n\n")
        human_message = input()
        if human_message in ["exit"]:
            return 
        print("================================== Human Query ==================================")
        print(human_message)
        print("\n")
        print("================================== Busqueda Semantica ==================================")
        results = PG_vector.simple_search(query=human_message, k=5)
        for i, doc in enumerate(results, 1):
            print(f"\nResultado {i}:")
            print(f"Contenido: {doc.page_content}")  # Primeros 200 caracteres
            print(f"Metadatos: {doc.metadata}")



if __name__=="__main__":
    from langchain_ollama import OllamaEmbeddings
    from dotenv import load_dotenv
    import os
    from pathlib import Path

    root = Path(__file__).resolve().parent
    collection_file = root / "mi_coleccion.txt"

    load_dotenv()
    SERVER_AI_URL = os.getenv("SERVER_AI_URL")

    model = "bge-m3:latest"
    embeddings_model = OllamaEmbeddings(model=model, base_url=SERVER_AI_URL)

    embedding_lengt = 1024

    main_(collection_file, embeddings_model, 1024)




