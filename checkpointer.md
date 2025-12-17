**Usa `graph.get_state(config)` con el mismo `thread_id` para recuperar el último estado del grafo después de la ejecución.**

El checkpointer (`InMemorySaver`) guarda **checkpoints** (snapshots del estado) en memoria por `thread_id`. Después de ejecutar el grafo, llama `graph.get_state(config)` para obtener el `StateSnapshot` más reciente, que contiene `values` (estado actual), `next` (siguientes nodos) y metadatos.

```python
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict

class State(TypedDict):
    foo: str
    bar: list[str]

# Tu grafo compilado
checkpointer = InMemorySaver()
graph = workflow.compile(checkpointer=checkpointer)

# Config con thread_id (¡IMPORTANTE: reutiliza el mismo!)
config = {"configurable": {"thread_id": "mi-thread-123"}}

# Ejecutar grafo
graph.invoke({"foo": "input"}, config=config)

# Recuperar ÚLTIMO estado (después de terminar)
state = graph.get_state(config)
print(state.values)  # {'foo': 'resultado-final', 'bar': ['a', 'b']}
print(state.next)    # () si terminó, o nodos pendientes
```

Para ver **historial completo** de checkpoints:

```python
history = list(graph.get_state_history(config))
latest = history[0]  # Primer elemento = más reciente
print(latest.values)
```

## Usar Postgres para Persistencia

**Sí, puedes guardar estados en Postgres con `PostgresSaver`.** Instala y configura:

```bash
pip install langgraph-checkpoint-postgres "psycopg[binary,pool]"
```

```python
from langgraph.checkpoint.postgres import PostgresSaver
import os

DB_URI = "postgresql://user:pass@localhost:5432/mydb?sslmode=disable"
checkpointer = PostgresSaver.from_conn_string(DB_URI)

# PRIMERA VEZ: crear tablas
checkpointer.setup()

graph = workflow.compile(checkpointer=checkpointer)

# Mismo uso: estados persisten en DB por thread_id
config = {"configurable": {"thread_id": "mi-thread-123"}}
graph.invoke({"foo": "input"}, config)
state = graph.get_state(config)  # Recupera de Postgres
```

Los estados quedan en tablas Postgres (`checkpoints`, `checkpoint_writes`) y persisten entre reinicios. Usa el mismo `thread_id` para recuperar.

**Nota:** `InMemorySaver` pierde datos al reiniciar el proceso. Postgres es para producción.

**Relevant docs:**
- [LangGraph Persistence](https://docs.langchain.com/oss/python/langgraph/persistence)
- [PostgresSaver](https://docs.langchain.com/oss/python/langgraph/persistence#langgraph-checkpoint-postgres)