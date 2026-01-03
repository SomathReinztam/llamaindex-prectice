from sqlalchemy.engine import Engine
from sqlalchemy import text
from typing import List



def get_db_tables(engine : Engine) -> List:
    query = text("""
    SELECT tablename FROM pg_tables 
    WHERE schemaname = 'public' 
    ORDER BY tablename;
    """)
    with engine.connect() as conn:
        response = conn.execute(query).fetchall()
    
    return [x[0] for x in response]



def get_all_collections(engine : Engine, db_name : str):
    query = text(f"""
    SELECT name
    FROM {db_name}_pg_collection;
    """)

    with engine.connect() as conn:
        response = conn.execute(query).fetchall()
    return [x[0] for x in response]





if __name__ == "__main__":
    from sqlalchemy import create_engine
    
    CONNECTION = "postgresql://langchain:langchain@localhost:5432/langchain"
    engine = create_engine(CONNECTION)

    response = get_db_tables(engine)
    print(response)

    # response = get_all_collections(engine=engine, db_name="langchain")
    # print(response)


