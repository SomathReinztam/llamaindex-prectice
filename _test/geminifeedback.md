Claro que sí. Para integrar **SQLAlchemy** con **PostgreSQL** y **pgvector** en tu flujo de trabajo, necesitamos hacer algunos ajustes.

El enfoque más eficiente no es llenar listas gigantes en memoria (que pueden saturar la RAM si el libro es largo), sino **insertar los registros en la base de datos a medida que procesas cada chunk**.

Aquí tienes la solución completa. He corregido algunos pequeños errores lógicos en tu bucle original (como el manejo de índices y el cierre del driver de Neo4j) e implementado la estructura de base de datos que pediste.

### Prerrequisitos

Necesitas instalar las librerías de conexión y manejo de vectores:

```bash
pip install sqlalchemy psycopg2-binary pgvector
```

### Código Modificado

Este script define las tablas y guarda los datos en Postgres y Neo4j simultáneamente.

```python
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from prompts import SYSTEM_ENTITY_RELATIONSHIP_EXTRACTION_PROMPT_1, HUMAN_ENTITY_RELATIONSHIP_EXTRACTION_PROMPT_1
from pathlib import Path
from dotenv import load_dotenv
import os
from neo4j import GraphDatabase

# --- Importaciones de SQLAlchemy ---
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import DeclarativeBase, sessionmaker, relationship, mapped_column
from pgvector.sqlalchemy import Vector

# ================== 
# 1. Configuración de Base de Datos (SQLAlchemy)
# ================== 

# Cadena de conexión basada en tu docker-compose
DATABASE_URL = "postgresql+psycopg2://langchain:langchain@localhost:5432/ragGraph"
engine = create_engine(DATABASE_URL)

class Base(DeclarativeBase):
    pass

# Tabla 1: Chunks
class ChunkModel(Base):
    __tablename__ = 'chunks'
    
    chunk_id = Column(Integer, primary_key=True, autoincrement=True)
    chunk_content = Column(Text)
    # bge-m3 suele tener 1024 dimensiones, ajusta el número si usas otro modelo
    embedding_chunk = Column(Vector(1024)) 
    
    # Relaciones para acceder desde el objeto (opcional pero útil)
    entities = relationship("EntityModel", back_populates="chunk")
    relations = relationship("RelationModel", back_populates="chunk")

# Tabla 2: Entities
class EntityModel(Base):
    __tablename__ = 'entities'
    
    entity_id = Column(Integer, primary_key=True, autoincrement=True)
    entity_name = Column(String)
    entity_type = Column(String)
    entity_description = Column(Text)
    entity_embedding = Column(Vector(1024))
    
    # Foreign Key
    entity_chunk_id = mapped_column(ForeignKey("chunks.chunk_id"))
    chunk = relationship("ChunkModel", back_populates="entities")

# Tabla 3: Relationships
class RelationModel(Base):
    __tablename__ = 'relationships'
    
    relation_id = Column(Integer, primary_key=True, autoincrement=True)
    relation_type = Column(String)
    relation_description = Column(Text)
    relation_embedding = Column(Vector(1024))
    
    # Foreign Key
    relation_chunk_id = mapped_column(ForeignKey("chunks.chunk_id"))
    chunk = relationship("ChunkModel", back_populates="relations")

# Crear las tablas en la base de datos
# NOTA: Asegúrate de haber ejecutado 'CREATE EXTENSION vector;' en tu DB antes, 
# o hazlo aquí con engine.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
try:
    with engine.connect() as conn:
        from sqlalchemy import text
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
except Exception as e:
    print(f"Nota: Asegúrate de que la extensión vector esté instalada. Error: {e}")

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# ================== 
# 2. Configuración de LangChain y Recursos
# ================== 

root = Path(__file__).resolve().parent.parent
book_file = root / "_docs" / "book.txt"

# Carga de documentos
text_loader = TextLoader(file_path=book_file)
docs = text_loader.load()

chunkenizer = RecursiveCharacterTextSplitter(chunk_size=3000, chunk_overlap=600)
chunks = chunkenizer.split_documents(docs)

load_dotenv()

SERVER_AI_URL = os.getenv("SERVER_AI_URL")
# Nota: bge-m3 genera vectores de 1024 dimensiones
model_emb = "bge-m3:latest" 
embedding = OllamaEmbeddings(model=model_emb, base_url=SERVER_AI_URL)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
model_llm = "openai/gpt-oss-120b" # Asegúrate que este nombre sea válido en Groq
llm = ChatGroq(model=model_llm, temperature=0.3, api_key=GROQ_API_KEY)

parser = JsonOutputParser()

# ======================
# 3. Funciones Neo4j
# ======================

def create_entity_cypher(name, label, description):
    query = """
    MERGE (e:Entity {name: $name})
    SET e.label = $label, e.description = $description
    """
    return query 

def create_relationship_cypher(source, target, rel_type, description):
    # Usamos type dinámico en Cypher con APOC o formateo de string seguro
    # Para simplificar aquí usamos formateo, pero cuidado con inyecciones si los datos no son limpios
    query = f"""
    MATCH (a:Entity {{name: $source}})
    MATCH (b:Entity {{name: $target}})
    MERGE (a)-[r:{rel_type}]->(b)
    SET r.description = $description
    """
    return query

URI = "bolt://localhost:7687"
USER = "neo4j"
PASSWORD = "langchain"
AUTH = (USER, PASSWORD)
driver = GraphDatabase.driver(URI, auth=AUTH)

# ======================
# 4. Procesamiento Principal
# ======================

print(f"Procesando {len(chunks)} chunks...")

try:
    for i, chunk in enumerate(chunks):
        print(f"Procesando Chunk {i+1}/{len(chunks)}")
        
        # 1. Crear el objeto Chunk para SQL
        chunk_text = chunk.page_content
        # Corrección: embed_query recibe un string, no un objeto Document
        chunk_vec = embedding.embed_query(chunk_text) 
        
        chunk_db = ChunkModel(
            chunk_content=chunk_text,
            embedding_chunk=chunk_vec
        )
        session.add(chunk_db)
        session.flush() # Esto genera el chunk_id automáticamente

        # 2. Extracción con LLM
        humam_message = HUMAN_ENTITY_RELATIONSHIP_EXTRACTION_PROMPT_1.format(text=chunk_text)
        messages = [
            SystemMessage(content=SYSTEM_ENTITY_RELATIONSHIP_EXTRACTION_PROMPT_1),
            HumanMessage(content=humam_message)
        ]
        
        try:
            ai_message = llm.invoke(messages)
            json_res = parser.parse(ai_message.content)
        except Exception as e:
            print(f"Error parseando LLM en chunk {i}: {e}")
            continue

        # 3. Procesar Entidades
        extracted_entities = json_res.get("entities", [])
        if extracted_entities:
            # Embeddings en batch para eficiencia
            ent_descriptions = [e.get("entity_description", "") for e in extracted_entities]
            ent_embeddings = embedding.embed_documents(texts=ent_descriptions)

            for j, entity in enumerate(extracted_entities):
                # Guardar en Postgres
                entity_db = EntityModel(
                    entity_name=entity.get("entity_name"),
                    entity_type=entity.get("entity_type"),
                    entity_description=entity.get("entity_description"),
                    entity_embedding=ent_embeddings[j],
                    entity_chunk_id=chunk_db.chunk_id # FK
                )
                session.add(entity_db)

                # Guardar en Neo4j
                with driver.session() as neo_session:
                    neo_session.run(
                        create_entity_cypher("", "", ""), # Usamos parametros mejor
                        parameters={
                            "name": entity.get("entity_name"), 
                            "label": entity.get("entity_type"), 
                            "description": entity.get("entity_description")
                        }
                    )
                    # Nota: Tu función original formateaba strings, aquí usé parámetros para 'name' 
                    # pero tu función create_entity original necesita ajuste para labels dinámicos 
                    # o usar la lógica original. Para mantener tu lógica original:
                    neo_session.run(create_entity(
                        entity.get("entity_name"), 
                        entity.get("entity_type"), 
                        entity.get("entity_description")
                    ))

        # 4. Procesar Relaciones
        extracted_relationships = json_res.get("relationships", [])
        if extracted_relationships:
            # Corrección: Usar la key correcta 'relationship_description'
            rel_descriptions = [r.get("relationship_description", "") for r in extracted_relationships]
            rel_embeddings = embedding.embed_documents(texts=rel_descriptions)

            for k, rel in enumerate(extracted_relationships):
                # Guardar en Postgres
                rel_db = RelationModel(
                    relation_type=rel.get("relationship_type"),
                    relation_description=rel.get("relationship_description"),
                    relation_embedding=rel_embeddings[k],
                    relation_chunk_id=chunk_db.chunk_id # FK
                )
                session.add(rel_db)

                # Guardar en Neo4j
                with driver.session() as neo_session:
                    neo_session.run(create_relationship(
                        rel.get("source_entity"),
                        rel.get("target_entity"),
                        rel.get("relationship_type"),
                        rel.get("relationship_description")
                    ))

        # Hacemos commit por cada chunk o grupo de chunks para guardar progreso
        session.commit()

finally:
    driver.close()
    session.close()
    print("Proceso finalizado.")
```

### Cambios Clave y Explicación:

1.  **Definición de Modelos (ORM):** He creado las clases `ChunkModel`, `EntityModel` y `RelationModel` que heredan de `DeclarativeBase`. Esto mapea automáticamente tus clases a las tablas de PostgreSQL.
2.  **`pgvector` Integration:** Se utiliza la columna `Vector(1024)` (asumiendo que `bge-m3` devuelve 1024 dim; si usa 768 u otro, cámbialo ahí). También se asegura de crear la extensión `vector` en la base de datos al inicio.
3.  **Gestión de Memoria:** He eliminado las listas globales (`chunk_id = []`, `chunk_content = []`, etc.). Ahora, los datos se instancian como objetos y se guardan en la base de datos dentro del bucle (`session.add(...)` y `session.commit()`).
4.  **Correcciones Lógicas del código original:**
    *   **Embeddings:** `embedding.embed_query` ahora recibe `chunk.page_content` (texto) en lugar del objeto `chunk` completo.
    *   **Clave foránea:** Usamos `chunk_db.chunk_id` obtenido tras el `session.flush()` para vincular entidades y relaciones con su chunk padre.
    *   **Driver Neo4j:** `driver.close()` se movió al bloque `finally` al final del script. Si lo dejas dentro del bucle, fallará en la segunda iteración.
    *   **Errores de tipeo:** Corregido el acceso a `relation["relationship_description"]` para generar embeddings.

Asegúrate de que tu contenedor Docker tenga la extensión vector activa (la imagen `pgvector/pgvector:pg16` ya la trae, pero el script de Python intenta activarla con `CREATE EXTENSION` por seguridad).