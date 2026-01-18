from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from connection.database import get_db
from connection.models import Category, Transaction, Source
from api.read_csv import router

app = FastAPI()
app.include_router(router)

@app.get("/categories")
def get_categories(db: Session = Depends(get_db)):
    return db.query(Category).all()

@app.get("/transactions")
def get_transactions(db: Session = Depends(get_db)):
    return db.query(Transaction).all()