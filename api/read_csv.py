import pandas as pd
from fastapi import FastAPI, File, UploadFile, APIRouter
from sqlalchemy.orm import Session
from connection.database import get_db
from connection.models import Category, Transaction, Source

router = APIRouter()

@router.post("/upload_csv/")
async def upload_csv (file: UploadFile = File(...)):
    content = await file.read()

    csv = pd.read_csv(content)
    colum_age = csv.count

    return colum_age