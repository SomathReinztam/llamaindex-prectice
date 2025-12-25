import requests
import json
from pathlib import Path

root = Path(__file__).resolve().parent


# URL del endpoint
url = "http://127.0.0.1:9621/documents/text"

# Datos a enviar
payload = {
    "file_source": "Source of the text (optional)",
    "text": "This is a sample text to be inserted into the RAG system."
}

# Encabezados
headers = None

# Enviar solicitud POST
try:
    response = requests.post(url, json=payload, headers=headers)
    
    # Verificar respuesta
    print(f"Código de estado: {response.status_code}")
    print(f"Respuesta: {response.text}")
    
    # Si necesitas procesar la respuesta como JSON
    if response.headers.get('Content-Type', '').startswith('application/json'):
        print(f"JSON: {response.json()}")
        
except requests.exceptions.ConnectionError:
    print("Error: No se pudo conectar al servidor. Verifica que esté corriendo en 127.0.0.1:9621")
except Exception as e:
    print(f"Error: {e}")