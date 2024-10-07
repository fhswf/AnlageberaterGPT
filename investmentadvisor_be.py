import io
import json
from typing import TypedDict, Annotated, Sequence

from PIL import Image
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.messages import ToolMessage, BaseMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
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
    messages: Annotated[Sequence[BaseMessage], add_messages]
    documents: Annotated[list[str], "Liste mit Dokumenten"]


# TypedDict
class InvestmentMetadata(TypedDict):
    """extrahierten Metadaten um ein passendes Produkt zu suchen"""

    mindestanlagebetrag: Annotated[int, ..., "Der Betrag den der Kunde anlegen möchte"]
    anlagedauer: Annotated[
        str, ..., "Die Dauer, wie lange der Kunde das Geld anlegen möchte (kurzfristig, mittelfristig, langfristig)"]
    risikobereitschaft: Annotated[
        str, ..., "Wie Risikobereit ist der Kunde (kein Risiko, mittleres Risiko, hohes Risiko"]


# Definiere Tool um Metadaten aus den Antworten des Anwenders zu extrahieren
@tool
def retrieve_metadata(prompt: str):
    """Bestimmt beziehungsweise extrahiert mithilfe GPT-Modell Metadaten aus den Antworten"""

    prompt = """Für die folgenden Fragen extrahierst du aus den Antworten Informationen zum Kunden, die später 
    benötigt werden: - Wieviel möchten Sie anlegen? Hier soll aus der Antwort nur der Betrag entnommen werden, 
    den der Kunde anlegen möchte. - Für wie lange können Sie das Geld anlegen (kurzfristig, mittelfristig, 
    langfristig)? Hier sollst du aus der Antwort des Kunden bestimmen, ob der Kunde kurzfristig, mittelfristig oder 
    langfristig anlegt. Antworte nur mit einem der Möglichkeiten. - Wie hoch ist Ihre Bereitschaft, Verluste in Kauf 
    zu nehmen? Hier sollst du die Risikobereitschaft aus der Antwort des Kunden auswerten. Hierfür sollst du eines 
    der Möglichkeiten ausgeben: kein Risiko, mittleres Risiko, hohes Risiko
    Der Kunde hat folgende Antworten (nacheinander) gegeben: """ + prompt

    structured_llm = llm.with_structured_output(InvestmentMetadata)
    answer = structured_llm.invoke(prompt)
    return {"messages": answer}


# ToDo: Umstrukturieren, sodass Langgraph den Workflow bestimmt und nicht GPT
# Definiere Tool um Metadaten aus den Antworten des Anwenders zu extrahieren
def get_productdata(state: AgentState):
    """Filtert mithilfe der extrahierten Metadaten die passenden Produktinformationen"""
    context = state["messages"][-1]
    metadata_json = json.loads(context.content)
    metadata_value = metadata_json["messages"]
    print(metadata_value)
    mindestanlagebetrag = metadata_value["mindestanlagebetrag"]
    anlagedauer = metadata_value["anlagedauer"]
    risikobereitschaft = metadata_value["risikobereitschaft"]

    vectordb_full_documents = Chroma(persist_directory="./chroma_langchain_db",
                                     collection_name="pdf_collection_documents",
                                     embedding_function=embeddings)

    # Filterung der Dokumente nach Metadaten
    retriever = vectordb_full_documents.as_retriever(
        search_kwargs={"filter": {
            '$and': [{'mindestanlagebetrag': {'$lte': mindestanlagebetrag}},
                     {'risiko': {'$eq': risikobereitschaft}}, {'laufzeit': {'$eq': anlagedauer}}]},
        })

    # Abfrage Daten aus Vektordatenbank
    retrieved_documents = retriever.invoke("")
    print(retrieved_documents)

    # prompt = PromptTemplate(
    #     template="""Du bist ein Anlageberater von der Musterbank eG und hast soeben ein passendes Produkt gefunden,
    #     dass dem Kunden angeboten werden kann. Nutze die folgenden abgerufene Dokumente, um kurz das Produkt
    #     vorzustellen und die relevanten Informationen zusammenzufassen. Es handelt sich hierbei um ein
    #     Produktinformationsblatt.
    #     Hier sind die Informationen zum Produkt: {context}""", input_variables=[context])
    #
    # llm_produktvorstellung = prompt | llm | StrOutputParser()
    # answer = llm_produktvorstellung.invoke({"context": retrieved_documents})

    return {"documents": retrieved_documents}


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


def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


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

    Rufe einen Tool auf, um die Metadaten aus den Antworten zu extrahieren. Anschließend soll mithilfe der Metadaten 
    das passende Dokument beziehungs Produktinformationsblatt gefunden werden, dass ein Produkt von der Bank 
    bewirbt. Stell das gefundene Produkt kurz vor und bewirb es als passendes Anlageprodukt für den Kunden."""

    if "documents" in state:
        documents = state["documents"]
        response = tool_llm.invoke([system_prompt] + state["messages"] + [format_docs(documents)])
    else:
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
workflow.add_node("product", get_productdata)

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

workflow.add_edge("tools", "product")
# We now add a normal edge from `tools` to `agent`.
# This means that after `tools` is called, `agent` node is called next.
workflow.add_edge("product", "agent")

# Now we can compile and visualize our graph
graph = workflow.compile()


testimg = graph.get_graph().draw_mermaid_png()
img = Image.open(io.BytesIO(testimg))
img.show()

# def print_stream(stream):
#     for s in stream:
#         message = s["messages"][-1]
#         if isinstance(message, tuple):
#             print(message)
#         else:
#             message.pretty_print()
#
#
# inputs = {"messages": [("user", "4000 €, kurzfristig, Ich gehe kein Risiko ein, Nein")]}
#
# print_stream(graph.stream(inputs, stream_mode="values"))

# ToDo: Bestimme Metadaten aus Antworten
# ToDo: Dynamische Suche mit Metadaten
