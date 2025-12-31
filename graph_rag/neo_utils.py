

# Crea un node del grafo
def create_entity(label: str):
    query = f"""
MERGE (e:{label} {{name: $name}})
SET e.description = $description
"""
    return query


# Crea una arista del grafo
def create_relationship(rel_type: str):
    query = f"""
MATCH (a {{name: $source}})
MATCH (b {{name: $target}})
MERGE (a)-[r:{rel_type}]->(b)
SET r.description = $description
"""
    return query



