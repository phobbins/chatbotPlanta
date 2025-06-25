from langchain.vectorstores import Chroma
from langchain.embeddings import SentenceTransformerEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import TextLoader


from langchain.document_loaders import PyPDFLoader, TextLoader
from langchain.document_loaders import DirectoryLoader

# Cargar todos los .txt y .pdf de una carpeta
def cargar_todos_los_documentos():
    directorio = "rag/documentos"

    loader_txt = DirectoryLoader(directorio, glob="*.txt", loader_cls=TextLoader)
    loader_pdf = DirectoryLoader(directorio, glob="*.pdf", loader_cls=PyPDFLoader)

    docs_txt = loader_txt.load()
    docs_pdf = loader_pdf.load()

    return docs_txt + docs_pdf


# Cargar y partir texto
def crear_vectorstore(path="documentos_hortensia.txt"):
    splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=50)
    chunks = splitter.split_documents(docs)

    embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
    db = Chroma.from_documents(chunks, embedding=embeddings, persist_directory="rag/chroma_db")

    return db
  

# Recuperar contexto
def recuperar_contexto_rag(pregunta, db, k=2):
    resultados = db.similarity_search(pregunta, k=k)
    return "\n".join([r.page_content for r in resultados])

def recuperar_contexto_rag(pregunta, db, k=2):
    resultados = db.similarity_search(pregunta, k=k)
    return "\n".join([r.page_content for r in resultados])

