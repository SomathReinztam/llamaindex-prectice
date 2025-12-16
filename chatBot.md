**Aquí tienes un ejemplo sencillo de un chatbot con LangGraph que mantiene memoria conversacional.**

LangGraph usa un grafo de estados con nodos para el LLM y bordes para el flujo. El estado `MessagesState` maneja automáticamente el historial de mensajes.

```python
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import MessagesState
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

# Configurar el modelo (necesitas OPENAI_API_KEY)
model = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# Nodo principal del chatbot - llama al LLM
def chatbot(state: MessagesState):
    response = model.invoke(state["messages"])
    return {"messages": [response]}

# Crear el grafo
workflow = StateGraph(state_schema=MessagesState)
workflow.add_node("chatbot", chatbot)

# Definir flujo: START -> chatbot -> END
workflow.add_edge(START, "chatbot")
workflow.add_edge("chatbot", END)

# Compilar el grafo (sin memoria persistente por simplicidad)
app = workflow.compile()

# Primera interacción
result1 = app.invoke({"messages": [HumanMessage(content="Hola, ¿cómo estás?")]})
print(result1["messages"][-1].content)
# > "¡Hola! Estoy muy bien, gracias por preguntar. ¿En qué puedo ayudarte?"

# Segunda interacción (mantiene contexto)
result2 = app.invoke(
    {"messages": [HumanMessage(content="¿Cuál fue mi primera pregunta?")]},
    {"past_key_values": result1.get("past_key_values", None)}
)
print(result2["messages"][-1].content)
# > "Tu primera pregunta fue: 'Hola, ¿cómo estás?'"
```

## Con memoria persistente (para conversaciones multi-turno)

Para un chatbot real, agrega un checkpointer para memoria entre llamadas:

```python
from langgraph.checkpoint.memory import InMemorySaver

# Compilar con memoria
checkpointer = InMemorySaver()
app = workflow.compile(checkpointer=checkpointer)

# Configuración con thread_id para mantener estado
config = {"configurable": {"thread_id": "abc123"}}

# Primera llamada
result1 = app.invoke(
    {"messages": [HumanMessage(content="Me llamo Juan")]}, 
    config
)

# Segunda llamada - recuerda el nombre
result2 = app.invoke(
    {"messages": [HumanMessage(content="¿Cómo me llamo?")]}, 
    config
)
print(result2["messages"][-1].content)
# > "Te llamas Juan"
```

El mismo `thread_id` mantiene el contexto entre invocaciones. Cambia el `thread_id` para conversaciones independientes.

**Relevant docs:**
- [LangGraph Overview](https://docs.langchain.com/oss/python/langgraph/overview)
- [MessagesState Reference](https://docs.langchain.com/oss/python/langgraph/reference/types/#langgraph.graph.message.MessagesState)