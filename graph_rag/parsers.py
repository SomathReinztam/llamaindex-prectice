from pydantic import BaseModel
from typing import Dict, Any

class Node(BaseModel):
    id : int
    entity_name : str
    entity_type : str
    entity_description : str
    metadata : Dict[str, Any]


class Relationship(BaseModel):
    source_entity : str
    target_entity: str
    relationship_type : str
    relationship_description : str
    metadata : Dict[str: Any]



