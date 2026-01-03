from sqlalchemy import text
from sqlalchemy.engine import Engine
from langchain_core.embeddings.embeddings import Embeddings
from typing import Tuple


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


# ejemplo de docs_index: (2, 5, 5, 9)
def get_relevant_documents(engine : Engine, docs_index : Tuple):
    idx = str(docs_index)
    SQL_QUERY = text("""
    SELECT
        chunk_content 
    FROM chunks
    WHERE
        chunk_id in (:idx);
    """)
    with engine.connect() as conn:
        response = conn.execute(
            SQL_QUERY,
            {"idx":idx}
        ).fetchall()
    return response





def simple_entitiy_retrive_2(engine : Engine, embedding : Embeddings, query : str, k : int):
    query_vec = embedding.embed_query(text=query)
    SQL_QUERY = text("""
    SELECT
        c.chunk_content AS text,
        c.chunk_id,
        e.entity_name,
        e.entity_type
        -(e.entity_embedding <#> (:query_vec)::vector) AS dot_similarity
    FROM 
        chunks c
    LEFT JOIN
        entities e ON c.chunk_id = e.entity_chunk_id
    ORDER BY 
        e.entity_embedding <#> (:query_vec)::vector ASC
    LIMIT :k;
    """)
    with engine.connect() as conn:
        response = conn.execute(
            SQL_QUERY,
            {"k":k, "query_vec":query_vec}
        ).fetchall()
    return response





def simple_entitiy_retrive_3(engine : Engine, embedding : Embeddings, query : str, k : int):
    query_vec = embedding.embed_query(text=query)
    SQL_QUERY = text("""
    SELECT
        c.chunk_id,
        c.chunk_content AS text,
        MAX(-(e.entity_embedding <#> (:query_vec)::vector)) AS dot_similarity
    FROM chunks c
    JOIN entities e
        ON c.chunk_id = e.entity_chunk_id
    GROUP BY c.chunk_id, c.chunk_content
    ORDER BY dot_similarity DESC
    LIMIT :k;
    """)
    with engine.connect() as conn:
        response = conn.execute(
            SQL_QUERY,
            {"k":k, "query_vec":query_vec}
        ).fetchall()
    return response






def simple_relation_retrive_3(engine : Engine, embedding : Embeddings, query : str, k : int):
    query_vec = embedding.embed_query(text=query)
    SQL_QUERY = text("""
    SELECT
        c.chunk_id,
        c.chunk_content AS text,
        MAX(-(r.relation_embedding <#> (:query_vec)::vector)) AS dot_similarity
    FROM chunks c
    JOIN relationships r
        ON c.chunk_id = r.relation_chunk_id
    GROUP BY c.chunk_id, c.chunk_content
    ORDER BY dot_similarity DESC
    LIMIT :k;
    """)
    with engine.connect() as conn:
        response = conn.execute(
            SQL_QUERY,
            {"k":k, "query_vec":query_vec}
        ).fetchall()
    return response