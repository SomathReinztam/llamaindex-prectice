from sqlalchemy import text
from sqlalchemy.engine import Engine
from langchain_core.embeddings.embeddings import Embeddings



def simple_entity_retrive(engine : Engine, embedding : Embeddings, query : str):
    query_vec = embedding.embed_query(text=query)

    SQL_QUERY = text("""
    SELECT
        entity_id,
        entity_name,
        entity_type,
        entity_chunk_id,
        -(entity_embedding <#> (:query_vec)::vector) AS dot_similarity
    FROM entities
    ORDER BY entity_embedding <#> (:query_vec)::vector ASC
    LIMIT 3;
    """)

    with engine.connect() as conn:
        response = conn.execute(
            SQL_QUERY,
            {"query_vec": query_vec}
        ).fetchall()
    
    return response





def simple_relation_retrive(engine : Engine, embedding : Embeddings, query : str):
    query_vec = embedding.embed_query(text=query)

    SQL_QUERY = text("""
    SELECT
        relation_id,
        relation_type,
        relation_chunk_id,
        -(relation_embedding <#> (:query_vec)::vector) AS dot_similarity
    FROM relationships
    ORDER BY relation_embedding <#> (:query_vec)::vector ASC
    LIMIT 3;
    """)

    with engine.connect() as conn:
        response = conn.execute(
            SQL_QUERY,
            {"query_vec": query_vec}
        ).fetchall()
    
    return response

