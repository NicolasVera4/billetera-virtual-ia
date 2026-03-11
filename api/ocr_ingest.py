import io
import pytesseract
from PIL import Image
from pdf2image import convert_from_bytes
import pypdf
from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session
from connection.database import get_db
from connection.models import Transaction, Category, TransactionType
import requests
import json
import re
from datetime import datetime, date

router_ocr = APIRouter()
OLLAMA_URL = "http://ollama:11434/api/generate"

def extract_text_from_file(contents: bytes, filename: str) -> str:
    name = filename.lower()

    if name.endswith((".png", ".jpg", ".jpeg")):
        img = Image.open(io.BytesIO(contents))
        return pytesseract.image_to_string(img)
    elif name.endswith(".pdf"):
        text = ""
        try:
            reader = pypdf.PdfReader(io.BytesIO(contents))
            for page in reader.pages:
                text += page.extract_text() or ""
        except Exception:
            text = ""
        if len(text.strip()) < 20:
            images = convert_from_bytes(contents)
            for img in images:
                text += pytesseract.image_to_string(img)
        
        return text
    else:
        raise ValueError(f"Formato incorrecto: {filename}")

def parse_transaction_from_text(text: str) -> dict:
    prompt = f""" Dado el siguiente texto extraído de una factura o recibo, extrae la información de la transacción.                                           

    Texto:
    {text}

    Responde ÚNICAMENTE con un JSON con este formato exacto:
    {{
        "fecha": "YYYY-MM-DD",
        "monto": 1234.56,
        "descripcion": "descripcion breve del gasto",
        "tipo": "expense",
        "categoria": "nombre de categoria en español"
    }}

    Para categoria te dejo algunas opciones de ejemplo: Comida, Transporte, Entretenimiento, Servicio Telefonico, Educacion, Otros, etc. 
    Si no podés determinar la fecha, usá la de hoy: {date.today().isoformat()}
    Si no podés determinar el tipo, usá "expense".
    Solo responde el JSON, sin texto adicional.
    """

    response = requests.post(OLLAMA_URL, json={
        "model": "mistral:7b",
        "prompt": prompt,
        "stream": False
    })
    raw = response.json().get("response", "")

    match = re.search(r'\{[\s\S]*\}', raw)
    if not match:
        raise ValueError(f"LLM no devolvio un JSON valido: {raw}")
    
    return json.loads(match.group())

@router_ocr.post("/upload_factura/")
async def upload_factura(file: UploadFile = File(...), db: Session = Depends(get_db)):
    contents = await file.read()

    try:
        text = extract_text_from_file(contents, file.filename)
    except ValueError as e:
        return {"error": str(e)}
    
    if not text.strip():
        return {"error": "No se puedo extraer texto"}

    try: 
        data = parse_transaction_from_text(text)
    except Exception as e:
        return {"error": f"Error al interpretar el texto: {str(e)}", "text_extracted": text}
    
    categoria_nombre = data.get("categoria", "Other")
    category = db.query(Category).filter(Category.name == categoria_nombre).first()
    if not category:
        category = Category(name=categoria_nombre)
        db.add(category)
        db.flush()
    
    tx = Transaction(
        amount=float(data["monto"]),
        description=data["descripcion"],
        transaction_date=datetime.strptime(data["fecha"], "%Y-%m-%d").date(),
        type=TransactionType(data["tipo"]),
        category_id=category.id
    )
    db.add(tx)
    db.commit()

    return {
        "message": "Transaccion insertada correctamente",
        "text_extracted": text,
        "transaction": data
    }