"""
Docstring for utils_pg.models

Este script al ejecutarse como main crea una base de datos llamada langchain de el ususario langchain con las siguientes tablas.

Nota.

Se supone que existe un usuario postgres llamado langchain y una base de datos llamado langchain
"""


from sqlalchemy import Column, Integer, String, Text, ForeignKey
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import DeclarativeBase, relationship, mapped_column

class Base(DeclarativeBase):
    pass

class ChunkModel(Base):
    __tablename__ = "chunks"

    chunk_id = Column(Integer, primary_key=True, autoincrement=True)
    chunk_content = Column(Text)
    # bge-m3 tiene 1024 dimenciones
    chunk_embedding = Column(Vector[1024])


    entities = relationship("EntityModel", back_populates="chunk")
    relations = relationship("RelationModel", back_populates="chunk")


class EntityModel(Base):
    __tablename__ = "entities"
    
    entity_id = Column(Integer, primary_key=True, autoincrement=True)
    entity_name = Column(String)
    entity_type = Column(String)
    entity_description = Column(Text)
    # bge-m3 tiene 1024 dimenciones
    entity_embedding = Column(Vector[1024])

    # Foreign Key
    entity_chunk_id = mapped_column(ForeignKey("chunks.chunk_id"))
    chunk = relationship("ChunkModel", back_populates="entities")


class RelationModel(Base):
    __tablename__ = "relationships"

    relation_id = Column(Integer, primary_key=True, autoincrement=True)
    relation_type = Column(String)
    relation_description = Column(Text)
    # bge-m3 tiene 1024 dimenciones
    relation_embedding = Column(Vector(1024))

    # Foreign Key
    relation_chunk_id = mapped_column(ForeignKey("chunks.chunk_id"))
    chunk = relationship("ChunkModel", back_populates="relations")


if __name__ == "__main__":
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import create_engine

    DATABASE_URL = "postgresql+psycopg2://langchain:langchain@localhost:5432/langchain"
    engine = create_engine(DATABASE_URL)

    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    session.close()
