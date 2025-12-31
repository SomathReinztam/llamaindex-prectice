### Idea del proyecto

```bash

|--graph_rag/
|          |-- prompts.py    # script que almacena prompts para extraccion de entidades/relaciones y los prompts para el chatbot de graph rag
|          |
|          |--
|
|--naive_rag/
|          |-- prompts.py     #
|
|-- make_naive_collection.py  # script encargado de cargar los documentos por ahora .txt, chunkenizar, e indexarlos en una db de postgres llamada naive_rag
|
|-- make_graph_collection.py  # script encargado de cargar documentos .txt por ahora, chunkenizar, extraer entidades y relaciones 
|                             # e indexarlas en una db llamada graph_rag, y guardar las entidades y relaciones tambien en neo4j
|
|

```

### Requirements


```bash
pip install python-dotenv
pip install langchain
pip install langchain_community
pip install langchain_postgres
pip install langchain-ollama
pip install neo4j 
pip install langchain_groq
pip install pyvis networkx


```


