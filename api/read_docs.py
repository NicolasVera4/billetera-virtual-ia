import io
import os
import json
import re
import pandas as pd
from groq import Groq
from fastapi import File, UploadFile, APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from connection.database import get_db
from connection.models import Category, Transaction, TransactionType

router = APIRouter()
MAX_ROWS = 500
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
GROQ_MODEL = "llama-3.1-8b-instant"

def call_llm(prompt: str) -> str:
     completion = groq_client.chat.completions.create(
          model=GROQ_MODEL,
          messages=[{"role": "user", "content": prompt}],
          temperature=0.1,
          stream=False
     )
     return completion.choices[0].message.content

def detect_and_read(filename, content) -> pd.DataFrame:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext == "xlsx":
        df = pd.read_excel(io.BytesIO(content), engine="openpyxl")
    elif ext in ("csv", ""):
        df = pd.read_csv(io.BytesIO(content))
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: .{ext}")
    return df.head(MAX_ROWS)

def extract_json(text: str) -> dict:
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        raise ValueError(f"No JSON found in LLM response: {text[:200]}")
    return json.loads(match.group())

def map_columns(columns: list, sample_rows: list[dict]) -> dict:
    prompt = f""" Tengo un archivo financiero con estas columnas: {columns}                                                                                    
    Ejemplo de datos (primeras 3 filas): {json.dumps(sample_rows, default=str)}                                                                                   
                                                                                                                                                                    
    Mapea las columnas a este schema de base de datos:                                                                                                            
    - transaction_date: columna con fecha de transacción                                                                                                          
    - amount: columna con monto/valor (si hay retiro/depósito separados, indica ambas)                                                                            
    - type: cómo determinar si es income o expense                                                                                                                
    - description: columna con descripción o concepto                                                                                                             
                                                                                                                                                                    
    Responde SOLO con este JSON, sin texto adicional:                                                                                                             
    {{                                                                                                                                                            
        "transaction_date": "nombre_columna",                                                                                                                       
        "amount_expense": "nombre_columna_o_null",                                                                                                                  
        "amount_income": "nombre_columna_o_null",                                                                                                                   
        "amount": "nombre_columna_o_null",                                                                                                                          
        "type_column": "nombre_columna_o_null",                                                                                                                     
        "type_mapping": {{"valor_original": "income_o_expense"}},                                                                                                   
        "description": "nombre_columna",                                                                                                                            
        "currency": "nombre_columna_o_null"                                                                                                                         
    }}                                                                                                                                                            
                                                                                                                                                                    
    Reglas:                                                                                                                                                       
    - Si hay una sola columna de monto, usa "amount" y pon null en amount_expense/amount_income.                                                                  
    - Si hay columnas separadas para retiro y depósito, usa amount_expense y amount_income y pon null en amount.                                                  
    - type_mapping mapea valores originales de type_column a "income" o "expense". Si no hay columna de tipo, pon type_column en null.                            
    - Si no hay columna de moneda, pon currency en null (se usará USD por defecto).  """
    
    raw = call_llm(prompt)
    return extract_json(raw)

def classify_descriptions_batch(descriptions: list[str], existing_categories: list[str]) -> dict:
    descs_text = "\n".join(f"- {d}" for d in descriptions)
    existing_text = ", ".join(existing_categories) if existing_categories else "(ninguna aun)"

    prompt = f"""Clasifica cada transacción en una categoría. Categorías existentes: {existing_text}                                                          
                Si ninguna categoría existente aplica, sugiere una nueva (1-2 palabras, bilingüe está bien).                                                                  
                                                                                                                                                                                
                Transacciones:                                                                                                                                                
                {descs_text}                                                                                                                                                  
                                                                                                                                                                                
                Responde SOLO con un JSON donde la clave es la descripción y el valor es la categoría. Ejemplo:                                                               
                {{"Office rent": "Rent", "Grocery shopping": "Supermarket"}}                                                                                                  
                """    

    raw = call_llm(prompt)
    try:
        return extract_json(raw)
    except (ValueError, json.JSONDecodeError):
        return {d: "Other" for d in descriptions} 

def get_or_create_category(name: str, db: Session) -> int:
    name = name.strip()
    category = db.query(Category).filter(Category.name.ilike(name)).first()
    if not category:
        category = Category(name=name)
        db.add(category)
        db.flush()
    return category.id 

def transform_and_insert(df: pd.DataFrame, mapping: dict, db: Session) -> dict:                                                                               
      desc_col = mapping["description"]                                                                                                                         
      date_col = mapping["transaction_date"]                                                                                                                    
      currency_col = mapping.get("currency")                                                                                                                    
      type_col = mapping.get("type_column")                                                                                                                     
      type_map = mapping.get("type_mapping") or {}                                                                                                              
      amount_col = mapping.get("amount")                                                                                                                        
      amount_expense_col = mapping.get("amount_expense")                                                                                                        
      amount_income_col = mapping.get("amount_income")                                                                                                          
                                                                                                                                                                
                                                                       

      new_rows_exist = False
      
      for _, row in df.iterrows():
          try:
              tx_date = pd.to_datetime(row[date_col]).date()
              description = str(row[desc_col]) if pd.notna(row[desc_col]) else ""

              if amount_col and pd.notna(row.get(amount_col)):
                  amount = abs(float(row[amount_col]))
              elif amount_expense_col or amount_income_col:
                  exp_val = float(row.get(amount_expense_col, 0) or 0) if amount_expense_col else 0
                  inc_val = float(row.get(amount_income_col, 0) or 0) if amount_income_col else 0
                  amount = abs(inc_val) if inc_val > 0 else abs(exp_val)
              else:
                  continue
              
              existing = db.query(Transaction).filter(
                  Transaction.transaction_date == tx_date,
                  Transaction.amount == amount,
                  Transaction.description == description
              ).first()
              if not existing:
                  new_rows_exist = True
                  break
          except:
              new_rows_exist = True
              break
      if not new_rows_exist:
          return {
              "message": "No hay transacciones nuevas, todos son duplicados",
              "inserted": 0,
              "skipped_duplicates": len(df),
              "categories_created": 0,
              "errors": [],
              "columns_detected": list(df.columns),
              "mapping_used": mapping
          }

      unique_descs = df[desc_col].dropna().astype(str).unique()[:50]
      existing_cats = [c.name for c in db.query(Category).all()]
      classification = classify_descriptions_batch(list(unique_descs), existing_cats)

      inserted = 0
      skipped = 0
      errors = []

      cat_cache = {}                                                                                                                                            
      for desc, cat_name in classification.items():                                                                                                             
          cat_cache[desc] = get_or_create_category(cat_name, db)                                                                                                
                                                                                                                                                                
      default_cat_id = get_or_create_category("Other", db)                                                                                                      
                                                                                                                                                                
      inserted = 0                                                                                                                                              
      errors = []                                                                                                                                               
      for idx, row in df.iterrows():                                                                                                                            
          try:                                                                                                                                                  
              tx_date = pd.to_datetime(row[date_col]).date()                                                                                                    
              description = str(row[desc_col]) if pd.notna(row[desc_col]) else ""                                                                               
                                                                                                                                                                
              if amount_col and pd.notna(row.get(amount_col)):                                                                                                  
                  amount = abs(float(row[amount_col]))                                                                                                          
                  if type_col and pd.notna(row.get(type_col)):                                                                                                  
                      raw_type = str(row[type_col]).strip().lower()                                                                                             
                      tx_type = type_map.get(raw_type, type_map.get(str(row[type_col]), "expense"))                                                             
                  else:                                                                                                                                         
                      tx_type = "expense" if float(row[amount_col]) >= 0 else "income"                                                                          
                                                                                                                                                                
              elif amount_expense_col or amount_income_col:                                                                                                     
                  exp_val = float(row.get(amount_expense_col, 0) or 0) if amount_expense_col else 0                                                             
                  inc_val = float(row.get(amount_income_col, 0) or 0) if amount_income_col else 0                                                               
                  if inc_val > 0:                                                                                                                               
                      amount = abs(inc_val)                                                                                                                     
                      tx_type = "income"                                                                                                                        
                  else:                                                                                                                                         
                      amount = abs(exp_val)                                                                                                                     
                      tx_type = "expense"                                                                                                                       
              else:                                                                                                                                             
                  continue                                                                                                                                      
                                                                                                                                                                
              currency = "USD"                                                                                                                                  
              if currency_col and pd.notna(row.get(currency_col)):                                                                                              
                  currency = str(row[currency_col]).strip().upper()                                                                                             
                                                                                                                                                                
              category_id = cat_cache.get(description, default_cat_id)                                                                                          
                                                                                                                                                                
              tx = Transaction(                                                                                                                                 
                  transaction_date=tx_date,                                                                                                                     
                  amount=amount,                                                                                                                                
                  currency=currency,                                                                                                                            
                  type=TransactionType(tx_type),                                                                                                                
                  description=description,                                                                                                                      
                  category_id=category_id,                                                                                                                      
              ) 

              existing = db.query(Transaction).filter(
                  Transaction.transaction_date == tx_date,
                  Transaction.amount == amount,
                  Transaction.description == description
              ).first()
              if existing:
                  errors.append(f"Row {idx}:  duplicado ignorado ({description})")
                  skipped += 1
                  continue
              
              db.add(tx)                                                                                                                                        
              inserted += 1                                                                                                                                     
          except Exception as e:                                                                                                                                
              errors.append(f"Row {idx}: {str(e)}")                                                                                                             
                                                                                                                                                                
      db.commit()                                                                                                                                               
                                                                                                                                                                
      result = {                                                                                                                                                
          "message": f"Successfully inserted {inserted} transactions",                                                                                          
          "inserted": inserted,
          "skipped_duplicates": skipped,                                                                                                                                 
          "categories_created": len(classification),                                                                                                            
      }                                                                                                                                                         
      if errors:                                                                                                                                                
          result["errors"] = errors[:10]                                                                                                                        
      return result                                                                                                                                                      

@router.post("/upload_data/")                                                                                                                                 
async def upload_data(file: UploadFile = File(...), db: Session = Depends(get_db)):  
    content = await file.read()
    
    try:
        df = detect_and_read(file.filename, content)
    except HTTPException:
        raise  
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading file: {str(e)}")
    
    if df.empty:
        raise HTTPException(status_code=400, detail="File is empty")
    
    sample_rows = df.head(3).to_dict(orient="records")
    mapping = map_columns(list(df.columns), sample_rows)

    result = transform_and_insert(df, mapping, db)
    result["columns_detected"] = list(df.columns)
    result["mapping_used"] = mapping
    return result