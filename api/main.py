import os
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from connection.database import get_db
from connection.models import Category, Transaction, Source, Document, AnomalyFlag
import shutil
from api.read_docs import router
from api.storage_docs import router_docs
from api.search_docs import search
from api.ask_user import router_rag
from api.agent.router import router_agent
from api.ocr_ingest import router_ocr
from api.ml_analisis import router_ml

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)
app.include_router(router_docs)
app.include_router(search)
app.include_router(router_rag)
app.include_router(router_agent)
app.include_router(router_ocr)
app.include_router(router_ml)

@app.get("/categories")
def get_categories(db: Session = Depends(get_db)):
    return db.query(Category).all()

@app.get("/transactions")
def get_transactions(db: Session = Depends(get_db)):
    return db.query(Transaction).all()

@app.delete("/reset/")
def reset_all(db: Session = Depends(get_db)):
    db.query(AnomalyFlag).delete()
    db.query(Transaction).delete()
    db.query(Document).delete()
    db.query(Category).delete()
    db.commit()

    try:
        import chromadb
        client = chromadb.HttpClient(host='chromadb', port=8000)
        client.delete_collection("documents")
        client.get_or_create_collection("documents")
    except Exception as e:
        pass

    uploads_dir = "/app/uploads"
    if os.path.exists(uploads_dir):
        shutil.rmtree(uploads_dir)
        os.makedirs(uploads_dir)

    return {"message": "Reset completado"}