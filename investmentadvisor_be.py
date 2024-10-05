import json
from typing import TypedDict, Annotated, Sequence

from IPython.core.display import Image
from dotenv import load_dotenv
from langchain_core.messages import ToolMessage, BaseMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langgraph.constants import END
from langgraph.graph import StateGraph, add_messages

load_dotenv()

# Auswahl Modell
llm_model = "gpt-4o"
embedding_model = "text-embedding-3-large"

llm = ChatOpenAI(model=llm_model)

# Initialisiere Vektordatenbank (Chroma) mit gespeicherten, vektorisierten Produktinformationen
embeddings = OpenAIEmbeddings(
    model=embedding_model)


class AgentState(TypedDict):
    """The state of the agent."""

    # add_messages is a reducer
    # See https://langchain-ai.github.io/langgraph/concepts/low_level/#reducers
    messages: Annotated[Sequence[BaseMessage], add_messages]


# Definiere Tool um Metadaten aus den Antworten des Anwenders zu extrahieren
@tool
def retrieve_metadata(prompt: str):
    """Extrahiert Metadaten aus den Antworten"""
    price = 5000
    return f"Das aktuelle Produkt hat den Preis ${price:.2f}"


# Liste mit allen Tools die verwendet werden sollen, um passendes Produkt zu finden
tools = [retrieve_metadata]

tool_llm = llm.bind_tools(tools)

tools_by_name = {tool.name: tool for tool in tools}


# Define our tool node
def tool_node(state: AgentState):
    outputs = []
    for tool_call in state["messages"][-1].tool_calls:
        tool_result = tools_by_name[tool_call["name"]].invoke(tool_call["args"])
        outputs.append(
            ToolMessage(
                content=json.dumps(tool_result),
                name=tool_call["name"],
                tool_call_id=tool_call["id"],
            )
        )
    return {"messages": outputs}


def call_model(
        state: AgentState
):
    # Erstelle Prompt fuer Tool-Calling Agent
    system_prompt = """Du bist ein digitaler Anlageberater und berätst Kunden zum Thema Vermögensanlage. Der Kunde 
    beantwortet mehrere Fragen, um mit dem sich ein Anlageprofil erstellen lässt. Zu den folgenden Fragen erhälst du 
    von dem Kunden jeweils eine Antwort:

    - Wieviel möchten Sie anlegen?
    - Für wie lange können Sie das Geld anlegen (kurzfristig, mittelfristig, langfristig)?
    - Wie hoch ist Ihre Bereitschaft, Verluste in Kauf zu nehmen?
    - Bevorzugen Sie bestimmte Anlageformen (z. B. Immobilien, Aktien, Anleihen, Kryptowährungen)?

    Rufe einen Tool auf, um die Metadaten aus den Antworten zu extrahieren."""

    response = tool_llm.invoke([system_prompt] + state["messages"])
    # We return a list, because this will get added to the existing list
    return {"messages": [response]}


# Define the conditional edge that determines whether to continue or not
def should_continue(state: AgentState):
    messages = state["messages"]
    last_message = messages[-1]
    # If there is no function call, then we finish
    if not last_message.tool_calls:
        return "end"
    # Otherwise if there is, we continue
    else:
        return "continue"


# Define a new graph
workflow = StateGraph(AgentState)

# Define the two nodes we will cycle between
workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)

# Set the entrypoint as `agent`
# This means that this node is the first one called
workflow.set_entry_point("agent")

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
        "continue": "tools",
        # Otherwise we finish.
        "end": END,
    },
)

# We now add a normal edge from `tools` to `agent`.
# This means that after `tools` is called, `agent` node is called next.
workflow.add_edge("tools", "agent")

# Now we can compile and visualize our graph
graph = workflow.compile()


# try:
#     img = Image(graph.get_graph().draw_mermaid_png())
# except Exception:
#     # This requires some extra dependencies and is optional
#     pass

def print_stream(stream):
    for s in stream:
        message = s["messages"][-1]
        if isinstance(message, tuple):
            print(message)
        else:
            message.pretty_print()


inputs = {"messages": [("user", "5000 €, kurzfristig, Ich habe eine hohe Bereitschaft, Nein")]}

print_stream(graph.stream(inputs, stream_mode="values"))

# ToDo: Ueber Langchain kann man die Fragen nicht nacheinander stellen (Sollte ueber UI geschehen)
# ToDo: Bestimme Metadaten aus Antworten
# ToDo: Dynamische Suche mit Metadaten

# vectordb = Chroma(persist_directory="./chroma_langchain_db", collection_name="pdf_collection",
#                   embedding_function=embeddings)

# Filterung der Dokumente nach Metadaten
# retriever = vectordb.as_retriever(
#     search_kwargs={"filter": {
#         '$and': [{'produktnummer': {'$eq': 10400552}}, {'risiko': {'$eq': 'Kein Risiko'}}]},
#         "k": 1})

# Abfrage Daten aus Vektordatenbank
# retrieved_documents = retriever.invoke("Wie hoch ist die Mindesteinlage?")
