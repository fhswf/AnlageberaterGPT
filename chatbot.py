import os
from dotenv import load_dotenv
from langchain.document_loaders import PyPDFLoader
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

llm_model = "gpt-4o"
embedding_model = "text-embedding-3-large"

folder_path = "Testdaten"

def load_pdfs_from_folder(folder_path):
    # Liste alle Dateien im Ordner auf
    pdf_files = [f for f in os.listdir(folder_path) if f.endswith('.pdf')]
    
    documents = []
    
    # Lese alle PDFs im Ordner ein
    for pdf_file in pdf_files:
        full_path = os.path.join(folder_path, pdf_file)
        loader = PyPDFLoader(full_path)
        documents.extend(loader.load())  # Füge die Dokumente hinzu
    
    return documents

documents = load_pdfs_from_folder(folder_path)

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=300, chunk_overlap=50)

chunks = text_splitter.split_documents(documents)

print(f"Split {len(documents)} documents into {len(chunks)} chunks.")

embeddings = OpenAIEmbeddings(
    model=embedding_model)

vector_store = Chroma.from_documents(
    documents=chunks,
    collection_name="pdf_collection",
    embedding=embeddings
)

retriever = vector_store.as_retriever()

# Abfrage Daten aus Vektordatenbank
""" retrieved_documents = retriever.invoke("Wie hoch ist die Mindesteinlage?")

# Zeige gefundene Datensätze aus Vektordatenbank
print(retrieved_documents[0].page_content)
print(retrieved_documents[0].metadata)
print(len(retrieved_documents)) """

llm = ChatOpenAI(model=llm_model)