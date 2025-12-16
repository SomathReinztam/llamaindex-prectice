from dotenv import load_dotenv
import os
from google import genai
from google_rag.rag_utils import (
    create_file_search_store
)


load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

client = genai.Client(api_key=API_KEY)
print("✅ Cliente inicializado correctamente")


# Crear nuestro primer store
store = create_file_search_store("Tutorial Gemini File Search - A Christmas Carol", client)



