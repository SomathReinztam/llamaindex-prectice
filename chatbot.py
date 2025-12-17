from dotenv import load_dotenv
import os
from prompts import SYSTEM_PROMPT

from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage
from langchain_ollama import ChatOllama

from typing import TypedDict, Annotated, Sequence
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

def create_chatModel():
    load_dotenv()
    SERVER_AI_URL = os.getenv("SERVER_AI_URL")
    model = "gpt-oss:20b"
    llm = ChatOllama(model=model, temperature=0.5, base_url=SERVER_AI_URL)

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


def run_conversation():
    chatbot = create_chatModel()
    messages = [SystemMessage(content=SYSTEM_PROMPT)]
    while True:
        human_message = input()
        if human_message in ["exit"]:
            return
        human_message = HumanMessage(content=human_message)
        print(human_message.pretty_repr())
        messages.append(human_message)
        response = chatbot.invoke({"messages":messages})
        messages = response["messages"]
        ai_message = messages[-1]
        print(ai_message.pretty_repr())
        


    
    

run_conversation()


