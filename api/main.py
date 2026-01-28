from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from connection.database import get_db
from connection.models import Category, Transaction, Source
from api.read_csv import router
from api.storage_docs import router_docs
from api.search_docs import search
from api.ask_user import router_rag
from api.agent.router import router_agent

app = FastAPI()
app.include_router(router)
app.include_router(router_docs)
app.include_router(search)
app.include_router(router_rag)
app.include_router(router_agent)

@app.get("/categories")
def get_categories(db: Session = Depends(get_db)):
    return db.query(Category).all()

@app.get("/transactions")
def get_transactions(db: Session = Depends(get_db)):
    return db.query(Transaction).all()