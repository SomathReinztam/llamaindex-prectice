```python
from sqlalchemy import create_engine

# Cadena de conexión
DATABASE_URL = "postgresql://usuario:contraseña@localhost:5432/nombre_bd"
connection = "postgresql://langchain:langchain@localhost:5432/langchain"

# Crear engine
engine = create_engine(connection)

# Probar conexión
with engine.connect() as conn:
    print("¡Conexión exitosa a PostgreSQL!")
```