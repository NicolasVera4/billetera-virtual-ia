import io
import os
import requests
from fastapi import FastAPI, File, UploadFile, APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from connection.database import get_db
from connection.models import Document, DocumentType
from pypdf import PdfReader
from datetime import datetime
import chromadb

router_docs = APIRouter()
UPLOAD_DIR = "/app/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

OLLAMA_URL = "http://ollama:11434/api/embed"                                                                                     
CHROMA_CLIENT = chromadb.HttpClient(host='chromadb', port=8000)
COLLECTION = CHROMA_CLIENT.get_or_create_collection(name="documents")

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 100

def split_text(text: str) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        chunks.append(text[start:end])
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks

def get_embedding(text: str) -> list:
    response = requests.post(
        OLLAMA_URL,
        json={"model": "nomic-embed-text", "input": text}
    )
    response.raise_for_status()
    return response.json()["embeddings"][0]

@router_docs.post("/upload_docs/")
async def upload_docs(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="tipo de archivo no valido")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    content = await file.read()

    with open(file_path, "wb") as f:
        f.write(content)

    reader = PdfReader(io.BytesIO(content))
    num_pages = len(reader.pages)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"

    document = Document(
        source_id=None,
        document_type=DocumentType.other,
        file_path=file_path,
        extracted_text=text
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    chunks = split_text(text)
    ids, embeddings, metadatas, docs = [], [], [], []
    for i, chunk in enumerate(chunks):
        embedding = get_embedding(chunk)
        ids.append(f"{document.id}_{i}")
        embeddings.append(embedding)
        metadatas.append({
            "document_id": document.id,
            "file_path": document.file_path,
            "document_type": "other",
            "chunk_index": i
        })
        docs.append(chunk)

    COLLECTION.add(ids=ids, embeddings=embeddings, metadatas=metadatas, documents=docs)

    return {
        "id": document.id,
        "file_path": document.file_path,
        "pages": num_pages,
        "chunks": len(chunks),
        "text_preview": text[:200] + "..." if len(text) > 200 else text,
        "message": "Documento procesado correctamente"
    }