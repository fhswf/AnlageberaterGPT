# Initialisiere Vektordatenbank (Chroma) mit gespeicherten, vektorisierten Produktinformationen
from typing import Optional

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_community.query_constructors.chroma import ChromaTranslator
from langchain_core.structured_query import Comparison, Comparator, Operator, Operation
from langchain_openai import OpenAIEmbeddings
from pydantic.v1 import BaseModel

load_dotenv()

# Test der RAG Funktionalitaet sowie Filter

class Search(BaseModel):
    mindestanlagebetrag: int
    risiko: Optional[str]
    laufzeit: Optional[str]


search_query = Search(mindestanlagebetrag=5000, risiko="kein Risiko", laufzeit="mittelfristig")


def construct_comparisons(query: Search):
    comparisons = []
    if query.mindestanlagebetrag is not None:
        comparisons.append(
            Comparison(
                comparator=Comparator.GT,
                attribute="mindestanlagebetrag",
                value=query.mindestanlagebetrag,
            )
        )
    if query.risiko is not None:
        comparisons.append(
            Comparison(
                comparator=Comparator.EQ,
                attribute="risiko",
                value=query.risiko,
            )
        )
    if query.laufzeit is not None:
        comparisons.append(
            Comparison(
                comparator=Comparator.EQ,
                attribute="laufzeit",
                value=query.laufzeit,
            )
        )
    return comparisons


comparisons = construct_comparisons(search_query)

_filter = Operation(operator=Operator.AND, arguments=comparisons)

print(ChromaTranslator().visit_operation(_filter))

embedding_model = "text-embedding-3-large"

embeddings = OpenAIEmbeddings(
    model=embedding_model)

vectordb = Chroma(persist_directory="./chroma_langchain_db", collection_name="pdf_collection_documents",
                  embedding_function=embeddings)

# Filterung der Dokumente nach Metadaten
retriever = vectordb.as_retriever(
    search_kwargs={"filter": {
        '$and': [{'produktnummer': {'$eq': 10400552}}, {'risiko': {'$eq': 'Kein Risiko'}}]},
    })

# Abfrage Daten aus Vektordatenbank
retrieved_documents = retriever.invoke("")
print(retrieved_documents)
