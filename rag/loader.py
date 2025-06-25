
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader, TextLoader, PyPDFLoader
from functools import partial
from langchain_huggingface import HuggingFaceEmbeddings




def cargar_todos_los_documentos():
    directorio = "rag/documentos"

    # Forzar UTF-8 al cargar archivos .txt
    loader_txt = DirectoryLoader(
        directorio,
        glob="*.txt",
        loader_cls=partial(TextLoader, encoding="utf-8")
    )

    loader_pdf = DirectoryLoader(
        directorio,
        glob="*.pdf",
        loader_cls=PyPDFLoader
    )

    docs_txt = loader_txt.load()
    docs_pdf = loader_pdf.load()

    return docs_txt + docs_pdf



# Cargar y partir texto
def crear_vectorstore(path="documentos_hortensia.txt"):
    docs=cargar_todos_los_documentos()
    splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=50)
    chunks = splitter.split_documents(docs)

    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    db = Chroma.from_documents(chunks, embedding=embeddings, persist_directory="rag/chroma_db")

    return db
  

# Recuperar contexto
def recuperar_contexto_rag(pregunta, db, k=2):
    resultados = db.similarity_search(pregunta, k=k)
    return "\n".join([r.page_content for r in resultados])

def recuperar_contexto_rag(pregunta, db, k=2):
    resultados = db.similarity_search(pregunta, k=k)
    return "\n".join([r.page_content for r in resultados])

