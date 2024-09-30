import os
import pandas as pd
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

# Auswahl Modell
llm_model = "gpt-4o"
embedding_model = "text-embedding-3-large"

folder_path = "testdaten"
csv_path = "produkteinstufung/ProduktMetadaten.csv"


# CSV-Datei einlesen (mit pandas) fuer Metadaten
def load_metadata_from_csv(path):
    return pd.read_csv(path, sep=';')


# Mapper Metadaten pro Dokument
def map_metadata(doc, metadaten):
    doc.metadata["produktname"] = metadaten["Produktname"].item()
    doc.metadata["produktnummer"] = metadaten["Produktnummer"].item()
    doc.metadata["mindestanlagebetrag"] = metadaten["Mindestanlagebetrag"].item()
    doc.metadata["laufzeit"] = metadaten["Laufzeit"].item()
    doc.metadata["risiko"] = metadaten["Risiko"].item()
    doc.metadata["gutschrift"] = metadaten["Gutschrift"].item()
    doc.metadata["kosten"] = metadaten["Kosten"].item()


def load_pdfs_from_folder(path):
    # Liste alle Dateien im Ordner auf
    pdf_files = [f for f in os.listdir(path) if f.endswith('.pdf')]

    # CSV-Datei laden
    metadata_df = load_metadata_from_csv(csv_path)

    # Initialisiere Liste fuer Dokumente
    document_list = []

    # Lese alle PDFs im Ordner ein
    for pdf_file in pdf_files:
        produkt_metadaten = metadata_df[metadata_df['Dateiname'] == pdf_file]
        full_path = os.path.join(path, pdf_file)
        loader = PyPDFLoader(full_path)
        document = loader.load()
        for doc in document:
            map_metadata(doc, produkt_metadaten)
        document_list.extend(document)  # Füge die Dokumente hinzu

    return document_list


documents = load_pdfs_from_folder(folder_path)

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=100, chunk_overlap=50)

chunks = text_splitter.split_documents(documents)

print(f"Split {len(documents)} documents into {len(chunks)} chunks.")

embeddings = OpenAIEmbeddings(
    model=embedding_model)

vector_store = Chroma.from_documents(
    documents=chunks,
    collection_name="pdf_collection",
    embedding=embeddings,
    persist_directory="./chroma_langchain_db"
)
