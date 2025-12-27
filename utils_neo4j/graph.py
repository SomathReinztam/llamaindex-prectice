
# Crea un node del grafo
def create_entity(name, label, description):
    query = """
MERGE (e:{label} {{name: '{name}'}})
SET e.description = '{description}'
    """
    return query.format(name=name, label=label, description=description)

# Crea una arista del grafo
def create_relationship(source, target, rel_type, description):
    query = """
MATCH (a {{name: '{source}'}})
MATCH (b {{name: '{target}'}})
MERGE (a)-[r:{rel_type}]->(b)
SET r.description = '{description}'
    """
    return query.format(source=source, target=target, rel_type=rel_type, description=description)
