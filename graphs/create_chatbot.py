from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage

from typing import TypedDict, Annotated, Sequence
from langgraph.graph.state import CompiledStateGraph
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

def create_chatModel(llm : BaseChatModel) -> CompiledStateGraph:

    class State(TypedDict):
        messages : Annotated[Sequence[BaseMessage], add_messages]


    def chat_node(state : State) -> State:
        messages = state["messages"]
        ai_response = llm.invoke(messages)
        return {"messages":ai_response}

    #checkpointer = MemorySaver()
    builder = StateGraph(State)

    builder.add_node("chat_node", chat_node)

    builder.add_edge(START, "chat_node")
    builder.add_edge("chat_node", END)

    #chatbot = builder.compile(checkpointer=checkpointer)
    chatbot = builder.compile()

    return chatbot