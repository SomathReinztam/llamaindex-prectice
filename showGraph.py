from neo4j import GraphDatabase
import networkx as nx
from pyvis.network import Network
import webbrowser  # Importamos para abrir el navegador
import os

def show_graph(uri, user, password):
    driver = GraphDatabase.driver(uri, auth=(user, password))
    G = nx.DiGraph()

    query = """
    MATCH (n)-[r]->(m)
    RETURN n, r, m
    """

    with driver.session() as session:
        result = session.run(query)

        for record in result:
            n = record["n"]
            m = record["m"]
            r = record["r"]

            # Usar element_id en lugar de id
            n_id = n.element_id
            m_id = m.element_id
            
            G.add_node(n_id, label=list(n.labels)[0] if n.labels else "Node", **dict(n))
            G.add_node(m_id, label=list(m.labels)[0] if m.labels else "Node", **dict(m))
            G.add_edge(n_id, m_id, label=r.type)

    driver.close()
    
    # Configurar pyvis para mejor visualización
    net = Network(
        notebook=False,  # Cambiar a False si no estás en Jupyter
        directed=True,
        height="750px",
        width="100%",
        bgcolor="#ffffff",
        font_color="black"
    )
    
    # Personalizar opciones de visualización
    net.set_options("""
    var options = {
      "nodes": {
        "font": {
          "size": 14
        }
      },
      "edges": {
        "arrows": {
          "to": {
            "enabled": true,
            "scaleFactor": 0.5
          }
        },
        "font": {
          "size": 12
        }
      },
      "physics": {
        "enabled": true
      }
    }
    """)
    
    net.from_nx(G)
    return net

if __name__ == "__main__":
    URI = "bolt://localhost:7687"
    USER = "neo4j"
    PASSWORD = "postgres"
    
    # Asegurarse que la contraseña sea correcta
    # PASSWORD = "tu_contraseña_real"  # "postgres" puede no ser la correcta
    
    try:
        # Generar el grafo
        net = show_graph(URI, USER, PASSWORD)
        
        # Guardar en archivo HTML
        output_file = "neo4j_graph.html"
        net.save_graph(output_file)
        
        # Ruta absoluta del archivo
        abs_path = os.path.abspath(output_file)
        print(f"Grafo generado exitosamente: {abs_path}")
        
        # Abrir automáticamente en el navegador
        webbrowser.open(f'file://{abs_path}')

        # Se crea el archivo: neo4j_graph.html
        # En Linux:
        # xdg-open neo4j_graph.html
        
    except Exception as e:
        print(f"Error: {e}")
        print("Verifica:")
        print("1. Que Neo4j esté corriendo (neo4j start)")
        print("2. Que la conexión sea correcta")
        print("3. Que las credenciales sean válidas")