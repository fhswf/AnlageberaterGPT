from typing import TypedDict, Annotated, Sequence

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.messages import HumanMessage, BaseMessage
from langgraph.graph import MessagesState, START, add_messages
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from pydantic import BaseModel
from langgraph.graph import END, StateGraph
from langgraph.checkpoint.memory import MemorySaver


# Test Agent mit Human-in-the-Loop, um nach Produktempfehlung fragen zuzulassen.
# Da Userinput bzw. Fragen als Tool-Message interpretiert werden, ist der Workflow nicht geeignet und wird fuer die
# Anwendung nicht verwendet. Stattdessen unterstuezt eine separate Funktion die Fragen.
load_dotenv()

embedding_model = "text-embedding-3-large"

# Initialisiere Vektordatenbank (Chroma) mit gespeicherten, vektorisierten Produktinformationen
embeddings = OpenAIEmbeddings(
    model=embedding_model)


def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


@tool
def rag(query: str):
    """Suche nach passendem Inhalt in den Dokumenten"""
    vectordb_chunks = Chroma(persist_directory="./chroma_langchain_db",
                             collection_name="pdf_collection_chunks",
                             embedding_function=embeddings)

    retriever = vectordb_chunks.as_retriever()

    document_chain = retriever | format_docs

    retrieved_documents = document_chain.invoke(query)
    return retrieved_documents


tools = [rag]
tool_node = ToolNode(tools)

# Set up the model

model = ChatOpenAI(model="gpt-4o")


# We are going "bind" all tools to the model
# We have the ACTUAL tools from above, but we also need a mock tool to ask a human
# Since `bind_tools` takes in tools but also just tool definitions,
# We can define a tool definition for `ask_human`
class AskHuman(BaseModel):
    """Ask the human a question"""

    question: str


model = model.bind_tools(tools + [AskHuman])


# Define the function that determines whether to continue or not
def should_continue(state):
    messages = state["messages"]
    last_message = messages[-1]
    # If there is no function call, then we finish
    if not last_message.tool_calls:
        return "end"
    # If tool call is asking Human, we return that node
    # You could also add logic here to let some system know that there's something that requires Human input
    # For example, send a slack message, etc
    elif last_message.tool_calls[0]["name"] == "AskHuman":
        return "ask_human"
    # Otherwise if there is, we continue
    else:
        return "continue"


# Define the function that calls the model
def call_model(state):
    messages = state["messages"]
    response = model.invoke(messages)
    # We return a list, because this will get added to the existing list
    return {"messages": [response]}


# We define a fake node to ask the human
def ask_human(state):
    pass


# Define a new graph
workflow = StateGraph(MessagesState)

# Define the three nodes we will cycle between
workflow.add_node("agent", call_model)
workflow.add_node("action", tool_node)
workflow.add_node("ask_human", ask_human)

# Set the entrypoint as `agent`
# This means that this node is the first one called
workflow.add_edge(START, "agent")

# We now add a conditional edge
workflow.add_conditional_edges(
    # First, we define the start node. We use `agent`.
    # This means these are the edges taken after the `agent` node is called.
    "agent",
    # Next, we pass in the function that will determine which node is called next.
    should_continue,
    # Finally we pass in a mapping.
    # The keys are strings, and the values are other nodes.
    # END is a special node marking that the graph should finish.
    # What will happen is we will call `should_continue`, and then the output of that
    # will be matched against the keys in this mapping.
    # Based on which one it matches, that node will then be called.
    {
        # If `tools`, then we call the tool node.
        "continue": "action",
        # We may ask the human
        "ask_human": "ask_human",
        # Otherwise we finish.
        "end": END,
    },
)

# We now add a normal edge from `tools` to `agent`.
# This means that after `tools` is called, `agent` node is called next.
workflow.add_edge("action", "agent")

# After we get back the human response, we go back to the agent
workflow.add_edge("ask_human", "agent")

memory = MemorySaver()

# Finally, we compile it!
# This compiles it into a LangChain Runnable,
# meaning you can use it as you would any other runnable
# We add a breakpoint BEFORE the `ask_human` node so it never executes
app = workflow.compile(checkpointer=memory, interrupt_before=["ask_human"])

config = {"configurable": {"thread_id": "2"}}
input_message = HumanMessage(
    content="Verwende rag tool um den Anwender zu fragen, ob dieser noch Fragen zum Produkt hat, um anschließend "
            "in den hinterlegten Dokumenten nach einer passenden Antwort zu suchen. Der Kunde darf unendlich viele "
            "Fragen stellen. Nachdem eine Frage beantwortet wurde, erhält der Kunde eine Antwort und anschließend "
            "sollen die Tools erneut aufgerufen werden, um weitere Fragen zu beantworten. Wenn sich der Kunde von dir "
            "verabschiedet und sich für die Produktberatung bedankt, kann der Prozess beendet werden."
)

for event in app.stream({"messages": [input_message]}, config, stream_mode="values"):
    event["messages"][-1].pretty_print()

tool_call_id = app.get_state(config).values["messages"][-1].tool_calls[0]["id"]

# We now create the tool call with the id and the response we want
tool_message = [
    {"tool_call_id": tool_call_id, "type": "tool", "content": "Wie hoch ist die Mindesteinlage?"}
]

# # This is equivalent to the below, either one works
# from langchain_core.messages import ToolMessage
# tool_message = [ToolMessage(tool_call_id=tool_call_id, content="san francisco")]

# We now update the state
# Notice that we are also specifying `as_node="ask_human"`
# This will apply this update as this node,
# which will make it so that afterwards it continues as normal
app.update_state(config, {"messages": tool_message}, as_node="ask_human")

# We can check the state
# We can see that the state currently has the `agent` node next
# This is based on how we define our graph,
# where after the `ask_human` node goes (which we just triggered)
# there is an edge to the `agent` node
# app.get_state(config).next

for event in app.stream(None, config, stream_mode="values"):
    event["messages"][-1].pretty_print()
#
# tool_call_id = app.get_state(config).values["messages"][-1].tool_calls[0]["id"]
#
# # We now create the tool call with the id and the response we want
# tool_message = [
#     {"tool_call_id": tool_call_id, "type": "tool", "content": "san francisco"}
# ]
#
# # # This is equivalent to the below, either one works
# # from langchain_core.messages import ToolMessage
# # tool_message = [ToolMessage(tool_call_id=tool_call_id, content="san francisco")]
#
# # We now update the state
# # Notice that we are also specifying `as_node="ask_human"`
# # This will apply this update as this node,
# # which will make it so that afterwards it continues as normal
# app.update_state(config, {"messages": tool_message}, as_node="ask_human")
#
# for event in app.stream(None, config, stream_mode="values"):
#     event["messages"][-1].pretty_print()
