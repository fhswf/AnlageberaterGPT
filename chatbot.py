from dotenv import load_dotenv
from langchain import langsmith
from langchain.document_loaders import PyPDFLoader
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

file_path = (
    "Testdaten\10400552_Festgeld_3_Monate.pdf"
)

loader = PyPDFLoader(file_path)

text_splitter = RecursiveCharacterTextSplitter(chunk_size=50, chunk_overlap=50)

embeddings = OpenAIEmbeddings(model="text-embedding-3-large")

vector_store = Chroma(
    collection_name="pdf_collection",
    embedding_function=embeddings
)