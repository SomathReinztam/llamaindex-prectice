import os
from dotenv import load_dotenv
from langchain_ollama import OllamaEmbeddings

load_dotenv()
SERVER_AI_URL = os.getenv("SERVER_AI_URL") # SERVER_AI_URL=http://10.8.0.11:11434/
model="bge-m3:latest"
embeddings_model = OllamaEmbeddings(model=model, base_url=SERVER_AI_URL)

input_text = "The meaning of life is 42"
vector = embeddings_model.embed_query(input_text)

print("\n")
print(f"type vector: {type(vector)}\n\n")
print(vector[:3])
print("\n\n")

text1 = "The cat sat on the mat"
text2 = "A feline rested on the carpet"
text3 = "Python is a programming language"
# Get embeddings using LangChain
embeddings = embeddings_model.embed_documents([text1, text2, text3])

print(f"type: {type(embeddings)} \n")
for x in embeddings:
    print(x[:3])



"""

curl -X POST http://10.8.0.11:11434/api/embeddings \
  -H "Content-Type: application/json" \
  -d '{
    "model": "bge-m3:latest",
    "prompt": "The meaning of life is 42"
  }'


"""