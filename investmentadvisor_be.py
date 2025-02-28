import json
from typing import TypedDict, Annotated, Sequence
from PIL import Image
import streamlit as st
from dotenv import load_dotenv
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
from langchain_chroma import Chroma
from langchain_core.messages import ToolMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langgraph.constants import END
from langgraph.graph import StateGraph, add_messages
from langchain_core.documents import Document
import io

load_dotenv()

# Auswahl Modell
llm_model = "gpt-4o"
embedding_model = "text-embedding-3-large"

llm = ChatOpenAI(model=llm_model)

# Initialisiere Vektordatenbank (Chroma) mit gespeicherten, vektorisierten Produktinformationen
embeddings = OpenAIEmbeddings(
    model=embedding_model)


class AgentState(TypedDict):
    """Initialisiere AgentState fuer Kommunikation im Graph"""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    documents: Annotated[list[str], "Liste mit Dokumenten"]


# TypedDict
class InvestmentMetadata(TypedDict):
    """extrahierten Metadaten um ein passendes Produkt zu suchen"""

    mindestanlagebetrag: Annotated[int, ..., "Der Betrag den der Kunde anlegen möchte"]
    laufzeit: Annotated[
        str, ..., "Die Dauer, wie lange der Kunde das Geld anlegen möchte (kurzfristig, mittelfristig, langfristig)"]
    risiko: Annotated[
        str, ..., "Wie Risikobereit ist der Kunde (kein Risiko, mittleres Risiko, hohes Risiko"]
    nachhaltigkeit: Annotated[
        str, ..., "Die Interesse des Kunden, ob er an nachhaltige Produkte interessiert ist (ja, nein)"]


# Definiere Tool um Metadaten aus den Antworten des Anwenders zu ermitteln
# Verwendung eines Few-Shot-Prompt für bessere Ermittlung der Metadaten
# Structured LLM: Ausgabe des LLM in Form von vordefinierter TypedDict
@tool
def retrieve_metadata(customer_input: str):
    """Extrahiert mithilfe GPT-Modell Metadaten aus den Antworten"""

    retrieve_metadata_system = """Du bist ein spezialisierter Anlageberater von einer Bank. Du ermittelst anhand der 
    gegebenen Fragen und den dazugehörigen Antworten die folgende Metadaten: Mindestanlagebetrag, Laufzeit, Risiko und 
    Nachhaltigkeit.
    \n 
    Der Mindestanlagebetrag startet von 0 € bis unendlich. Den Betrag ermittelst du aus der Antwort der Frage: Wie viel 
    möchten Sie anlegen? 
    \n 
    Bei der Laufzeit gibt es drei Möglichkeiten: kurzfristig, mittelfristig oder langfristig. Die Laufzeit bestimmst du 
    aus der Antwort der Frage: Für wie lange können Sie das Geld anlegen (kurzfristig, mittelfristig, langfristig)? 
    \n 
    Das Risiko teilt sich in drei Kategorien auf: kein Risiko, mittleres Risiko oder hohes Risiko. Die richtige 
    Risikoklasse ermittelst du aus den Antworten mehrerer Fragen: "Wie würden Sie Ihre Risikobereitschaft einschätzen 
    (z. B. kein Risiko, mittleres Risiko, hohes Risiko?" und "Haben Sie in der Vergangenheit bereits riskante 
    Investments getätigt (z. B. Aktien, Derivate) und wie haben Sie sich dabei gefühlt? 
    \n 
    Bei der Nachhaltigkeit gibt es zwei Möglichkeiten, ja oder nein. Die Antwort bestimmst du aus der Frage: Insofern 
    in unserem Produktportfolio vorhanden, interessieren Sie sich für nachhaltige Anlageprodukte? 
    \n\n 
    Hier sind ein paar Beispiele für ermittelte Metadaten: 
    \n 
    example_user: Wieviel möchten Sie anlegen? Ich möchte 4000 € anlegen example_assistant: mindestanlagebetrag: 4000 
    \n 
    example_user: Wieviel möchten Sie anlegen? Ich habe noch keine Vorstellung wieviel ich anlegen möchte 
    example_assistant: mindestanlagebetrag: 0 
    \n 
    example_user: Für wie lange können Sie das Geld anlegen (kurzfristig, mittelfristig, langfristig)? Ich kann mein 
    Geld für eine längere Zeit anlegen. 
    example_assistant: laufzeit: "langfristig"
    \n 
    example_user: Für wie lange können Sie das Geld anlegen (kurzfristig, mittelfristig, langfristig)? Ich kann mein 
    Geld für ein paar Monate anlegen 
    example_assistant: laufzeit: "mittelfristig" """

    prompt = ChatPromptTemplate.from_messages([("system", retrieve_metadata_system), ("human", "{input}")])
    structured_llm = llm.with_structured_output(InvestmentMetadata)
    few_shot_structured_llm = prompt | structured_llm

    answer = few_shot_structured_llm.invoke(customer_input)
    return {"messages": answer}


# Funktion, die das passende Dokument zurückgibt
def finde_passendes_dokument(nachhaltigkeit_gewünscht: str, dokumente: Document):
    # Zuerst filtern wir die nachhaltigen Produkte, falls der Kunde das möchte
    if nachhaltigkeit_gewünscht == "ja":
        nachhaltige_dokumente = [doc for doc in dokumente if doc.metadata.get("nachhaltigkeit") == "ja"]

        # Wenn ein nachhaltiges Dokument vorhanden ist, geben wir es zurück
        if nachhaltige_dokumente:
            return nachhaltige_dokumente[0]

    # Wenn kein nachhaltiges Produkt gefunden wurde oder der Kunde keine Präferenz hat,
    # nehmen wir das erste verfügbare Produkt
    return dokumente[0]


# Definiere Tool um Metadaten aus den Antworten des Anwenders zu extrahieren
def get_productdata(state: AgentState):
    """Filtert mithilfe der extrahierten Metadaten die passenden Produktinformationen"""
    context = state["messages"][-1]
    metadata_json = json.loads(context.content)
    metadata_value = metadata_json["messages"]
    print(metadata_value)
    mindestanlagebetrag = metadata_value["mindestanlagebetrag"]
    laufzeit = metadata_value["laufzeit"]
    risiko = metadata_value["risiko"]
    nachhaltigkeit = metadata_value["nachhaltigkeit"]

    vectordb_full_documents = Chroma(persist_directory="./chroma_langchain_db",
                                     collection_name="pdf_collection_documents",
                                     embedding_function=embeddings)

    # Filterung der Dokumente nach Metadaten
    retriever = vectordb_full_documents.as_retriever(
        search_kwargs={"filter": {
            '$and': [{'mindestanlagebetrag': {'$lte': mindestanlagebetrag}}, {'laufzeit': {'$eq': laufzeit}},
                     {'risiko': {'$eq': risiko}}]},
        })

    # Abfrage Daten aus Vektordatenbank
    retrieved_documents = retriever.invoke("")

    if retrieved_documents:
        filtered_document = finde_passendes_dokument(nachhaltigkeit, retrieved_documents)
        document_metadata = filtered_document.metadata
        st.session_state.produktnummer = document_metadata.get("produktnummer")
        st.session_state.document_path = document_metadata.get("source")
        st.session_state.empty_product = False
    print(retrieved_documents)

    return {"documents": retrieved_documents}


# Liste mit allen Tools die verwendet werden sollen, um passendes Produkt zu finden
tools = [retrieve_metadata]

tool_llm = llm.bind_tools(tools)

tools_by_name = {tool.name: tool for tool in tools}


# Definiere Tool Node
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


def agent_product_node(
        state: AgentState
):
    # Erstelle Prompt fuer Tool-Calling Agent
    system_prompt = """Du bist ein digitaler Anlageberater von der Musterbank eG und berätst Kunden zum Thema 
    Vermögensanlage. Der Kunde beantwortet mehrere Fragen, mit dem sich ein Anlageprofil erstellen lässt. Zu den 
    folgenden Fragen erhälst du von dem Kunden Antworten:

    - Wie viel möchten Sie anlegen?
    - Für wie lange können Sie das Geld anlegen (kurzfristig, mittelfristig, langfristig)?
    - Wie würden Sie Ihre Risikobereitschaft einschätzen (z. B. kein Risiko, mittleres Risiko, hohes Risiko)?
    - Haben Sie in der Vergangenheit bereits riskante Investments getätigt (z. B. Aktien, Derivate) und wie haben Sie 
    sich dabei gefühlt?
    - Insofern in unserem Produktportfolio vorhanden, interessieren Sie sich für nachhaltige Anlageprodukte?

    Rufe einen Tool auf, um die Metadaten aus dem Input (Fragen und Antworten) zu extrahieren. Anschließend soll 
    mithilfe der Metadaten ein passendes Dokument beziehungsweise Produktinformationsblatt gefunden werden, 
    dass ein Produkt von der Bank bewirbt. Stell das gefundene Produkt kurz vor und bewirb es auf Basis der Antworten 
    als passendes Anlageprodukt für den Kunden."""

    print(state["messages"])

    if "documents" in state and st.session_state.empty_product is False:
        documents = state["documents"]
        response = tool_llm.invoke([system_prompt] + state["messages"] + [format_docs(documents)])
        st.session_state.messages.append({"role": "assistant", "content": response.content})
    elif "documents" in state and st.session_state.empty_product:
        response = {"role": "assistant", "content": "Kein passendes Produkt gefunden!"}
    else:
        response = tool_llm.invoke([system_prompt] + state["messages"])
    return {"messages": [response]}


# Definiere Funktion die das naechste vorgehen (ja nach Kondition) dynamisch bestimmt
def should_continue(state: AgentState):
    messages = state["messages"]
    last_message = messages[-1]
    # Wenn kein Tool aufgerufen wird, dann gilt der Graph-Workflow als beendet
    if not last_message.tool_calls:
        return "end"
    # Alternativ wird der Workflow weiter durchgefuehrt
    else:
        return "continue"


# Definiere einen neuen Graph
workflow = StateGraph(AgentState)

# Definiere alle Nodes, zwischen denen kommuniziert wird
workflow.add_node("agent", agent_product_node)
workflow.add_node("tools", tool_node)
workflow.add_node("product", get_productdata)

# Setze Einstieg auf `agent`. Der Graph bzw. Prozess startet dementsprechend beim Agent
workflow.set_entry_point("agent")

# Bestimme dynamische Kante im Graph. Der Graph ruft entweder ein Tool auf oder beendet den Prozess
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "continue": "tools",
        "end": END,
    },
)

# Setzen einer Kante von `tools` zur `product` node, um mithilfe der Metadaten passende Dokumente zu suchen
workflow.add_edge("tools", "product")

# Setzen einer Kante von `product` zur `agent` node, um gefundenes Dokument/Produkt an Agent zu uebergeben
workflow.add_edge("product", "agent")

# Compile Graph
graph = workflow.compile()


# Erstelle Graph
# testimg = graph.get_graph().draw_mermaid_png()
# img = Image.open(io.BytesIO(testimg))
# img.show()

def print_stream(stream):
    for s in stream:
        message = s["messages"][-1]
        if isinstance(message, tuple):
            print(message)
        else:
            message.pretty_print()


# Methode um Graph aufzurufen
def call_graph(answers: str):
    inputs = {"messages": [("user", answers)]}

    print_stream(graph.stream(inputs, stream_mode="values"))


# RAG-Funktion um fuer Kundenfragen eine Antwort auf Basis der Produktinformationen zu dokumentieren
def answer_with_rag(user_query: str):
    vectordb_chunks = Chroma(persist_directory="./chroma_langchain_db",
                             collection_name="pdf_collection_chunks",
                             embedding_function=embeddings)

    retriever = vectordb_chunks.as_retriever(
        search_kwargs={"filter": {"produktnummer": st.session_state.produktnummer}})

    system_prompt = """Du bist ein Anlageberater von der Musterbank eG und beantwortest die Fragen von Kunden.
    Verwende die Chat Historie als auch den retrieved context um die Fragen des Bankkunden zu beantworten. Wenn du
    die Antwort nicht weißt, sag dem Kunden, dass du die Informationen nachlieferst. Halte die Antwort so knapp wie
    möglich.
    Context: {context}"""

    qa_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )

    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)

    rag_chain = create_retrieval_chain(retriever, question_answer_chain)
    response_qa = rag_chain.invoke({"input": user_query, "chat_history": st.session_state.messages})
    st.session_state.messages.append({"role": "assistant", "content": response_qa["answer"]})

    return response_qa["answer"]
