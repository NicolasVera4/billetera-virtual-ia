import io
import os
import requests
import pandas as pd
from fastapi import FastAPI, File, UploadFile, APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from connection.database import get_db
from connection.models import Category, Transaction, Source, TransactionType, Document, DocumentType
from pypdf import PdfReader
from datetime import datetime

router_docs = APIRouter()
UPLOAD_DIR = "/app/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

OLLAMA_URL = "http://ollama:11434/api/embed"                                                                                     
                                                                                                                                                                
def get_embedding(text: str) -> list:                                                                                                                         
      response = requests.post(                                                                                                                                 
          OLLAMA_URL,                                                                                                                                           
          json={                                                                                                                                                
              "model": "nomic-embed-text",                                                                                                                      
              "input": text                                                                                                          
          }                                                                                                                                                     
      )                                                                                                                                                         
      response.raise_for_status()                                                                                                                               
      return response.json()["embeddings"][0]  

@router_docs.post("/upload_docs/")
async def upload_docs(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code= 400,
            detail= "tipo de archivo no valido"
        )

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

    documents = Document(
        source_id=2,                                                                                                 
        document_type=DocumentType.invoice,                                                                                                 
        file_path=file_path,                                                                                                                                      
        extracted_text=text 
    )
    db.add(documents)
    db.commit()
    db.refresh(documents)

    embedding = get_embedding(text)

    return {                                                                                                                                                      
      "id": documents.id,                                                                                                                                        
      "file_path": documents.file_path,                                                                                                                          
      "pages": num_pages,                                                                                                                                       
      "text_preview": text[:200] + "..." if len(text) > 200 else text,
      "embedding_size": len(embedding),                                                                                          
      "message": "Documento procesado correctamente"                                                                                                            
    }   