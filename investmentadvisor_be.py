from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings

load_dotenv()

# Auswahl Modell
llm_model = "gpt-4o"
embedding_model = "text-embedding-3-large"

# Initialisiere Vektordatenbank (Chroma) mit gespeicherten, vektorisierten Produktinformationen
embeddings = OpenAIEmbeddings(
    model=embedding_model)

vectordb = Chroma(persist_directory="./chroma_langchain_db", collection_name="pdf_collection",
                  embedding_function=embeddings)

llm = ChatOpenAI(model=llm_model)

# ToDo: Ueber Langchain kann man die Fragen nicht nacheinander stellen (Sollte ueber UI geschehen)

# ToDo: Ab hier dynamische Suche mit Metadaten
# Filterung der Dokumente nach Metadaten
# retriever = vectordb.as_retriever(
#     search_kwargs={"filter": {
#         '$and': [{'produktnummer': {'$eq': 10400552}}, {'risiko': {'$eq': 'Kein Risiko'}}]},
#         "k": 1})

# Abfrage Daten aus Vektordatenbank
# retrieved_documents = retriever.invoke("Wie hoch ist die Mindesteinlage?")

# Zeige gefundene Datensätze aus Vektordatenbank
# print(retrieved_documents)
# print(len(retrieved_documents))


# ToDo: Bestimme Metadaten aus Antworten
# def evaluate_answers():
#     model = ChatOpenAI(model=llm_model)
#     system_template = "Translate the following into {language}:"
#
#     parser = StrOutputParser()
#
#     prompt_template = ChatPromptTemplate.from_messages(
#         [("system", system_template), ("user", "{text}")]
#     )
#
#     chain = prompt_template | model | parser
#
#     result = chain.invoke({"language": "italian", "text": "hi"})
#
#     print(result)
