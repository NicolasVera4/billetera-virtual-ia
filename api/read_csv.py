import io
import pandas as pd
from fastapi import FastAPI, File, UploadFile, APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from connection.database import get_db
from connection.models import Category, Transaction, Source, TransactionType


router = APIRouter()

@router.post("/upload_csv/")
async def upload_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()

    try:
        df = pd.read_csv(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al leer csv: {str(e)}")

    required_columns = ["transaction_date","amount","currency","type","category","description","source"]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise HTTPException(status_code=400, detail=f"Missing columns: {missing_columns}")
    
    inserted = 0
    for _, row in df.iterrows():
        transaction = Transaction(
            source_id=row.get("source_id"),
            transaction_date=row["transaction_date"],
            amount=row["amount"],
            currency=row.get("currency", "USD"),
            type=TransactionType(row["type"]),
            category_id=row.get("category_id"),
            description=row.get("description")
        )
        db.add(transaction)
        inserted += 1
    db.commit()

    return {"message": f"Sussefully inserted {inserted} transactions"}