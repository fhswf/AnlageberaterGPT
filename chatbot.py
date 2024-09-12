from dotenv import load_dotenv
from langchain.document_loaders import PyPDFLoader
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

embedding_model = "text-embedding-3-large"

file_path = (
    "Testdaten/10400552_Festgeld_3_Monate.pdf"
)

loader = PyPDFLoader(file_path)

docs = loader.load()

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=300, chunk_overlap=50)

chunks = text_splitter.split_documents(docs)

print(f"Split {len(docs)} documents into {len(chunks)} chunks.")

embeddings = OpenAIEmbeddings(
    model=embedding_model)

vector_store = Chroma.from_documents(
    documents=chunks,
    collection_name="pdf_collection",
    embedding=embeddings
)

retriever = vector_store.as_retriever()

retrieved_documents = retriever.invoke("Wie hoch ist die Mindesteinlage?")

# Zeige gefundene Datensätze aus Vektordatenbank
print(retrieved_documents[0].page_content)
print(retrieved_documents[0].metadata)
print(len(retrieved_documents))