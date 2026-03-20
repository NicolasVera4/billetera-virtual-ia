from sqlalchemy.orm import Session
from sqlalchemy import extract
from connection.database import get_db
from connection.models import Transaction, Category, TransactionType
from datetime import datetime, date
import chromadb
import requests

OLLAMA_URL = "http://ollama:11434/api/embed"                                                                                                                  
CHROMA_CLIENT = chromadb.HttpClient(host='chromadb', port=8000)                                                                                               
COLLECTION = CHROMA_CLIENT.get_or_create_collection(name="documents")  

TOOLS = [                                                                                                                                                     
      {                                                                                                                                                         
          "name": "search_documents",                                                                                                                           
          "description": "Busca información en documentos financieros (facturas, recibos). Usar cuando preguntan sobre contenido de documentos.",               
          "parameters": ["query"]                                                                                                                               
      },                                                                                                                                                        
      {                                                                                                                                                         
          "name": "query_transactions",                                                                                                                         
          "description": "Consulta transacciones por categoría o tipo. Usar cuando preguntan sobre gastos, ingresos o montos.",                                 
          "parameters": ["category", "type", "month", "year"]                                                                                                                    
      },                                                                                                                                                        
      {                                                                                                                                                         
          "name": "get_summary",                                                                                                                                
          "description": "Obtiene resumen financiero con totales. Usar cuando piden balance, totales o resumen general.",                                       
          "parameters": ["month", "year"]                                                                                                                                      
      },                                                                                                                                                        
      {                                                                                                                                                         
          "name": "list_categories",                                                                                                                            
          "description": "Lista todas las categorías disponibles. Usar cuando preguntan qué categorías existen.",                                               
          "parameters": []                                                                                                                                      
      },
      {
           "name": "insert_transaction",
           "description": "Registra una nueva transacción. Usar cuando el usuario dice que gastó, pagó, cobró o recibió dinero. Ejemplo: 'gasté 500 en el supermercado'.",
           "parameters": ["amount", "description", "type", "category", "date_str"]
      },
      {
           "name": "get_max_expense",
           "description": "Obtiene el mayor gasto registrado. Usar cuando preguntan cual fue el mayor gasto, la transaccion mas cara o ell gasto mas alto.",
           "parameters": ["month", "year"]
      },  
      {
           "name": "get_max_income",
           "description": "Obtiene el mayor ingreso registrado. Acepta filtros opcionales de mes y año.",
           "parameters": {
                "month": "numero de mes (1-12), opcional",
                "year": "año (ej: 2026), opcional"
           }
      },
      {                                                                                                                                                           
           "name": "get_top_expenses",                                                                                                                               
           "description": "Obtiene los N gastos más altos ordenados por monto. Usar cuando preguntan por los mayores gastos, los más caros o top gastos.",           
           "parameters": ["limit", "month", "year"]                                                                                                                  
      },                                                                                                                                                            
      {                                                                                                                                                             
           "name": "get_category_summary",                                                                                                                           
           "description": "Obtiene un resumen detallado de una categoría: total, cantidad, promedio y detalle de transacciones.",                                  
           "parameters": ["category", "month", "year"]                                                                                                               
      }                                                                                                                                                       
]

def get_embedding(text: str) -> str:
    response = requests.post(
        OLLAMA_URL,
        json={"model": "nomic-embed-text", 
              "input": text[:8000]
             }
    )
    response.raise_for_status()
    return response.json()["embeddings"][0]

def tool_search_documents(query: str) -> str:
      query_embedding = get_embedding(query)                                                                                                                    
      results = COLLECTION.query(                                                                                                                               
          query_embeddings=[query_embedding],                                                                                                                   
          n_results=3,                                                                                                                                          
          include=["documents", "metadatas"]                                                                                                                    
      )                                                                                                                                                         
                                                                                                                                                                
      if not results["documents"][0]:                                                                                                                           
          return "No encontré documentos relevantes."                                                                                                           
                                                                                                                                                                
      docs = []                                                                                                                                                 
      for i, doc in enumerate(results["documents"][0]):                                                                                                         
          meta = results["metadatas"][0][i]                                                                                                                     
          docs.append(f"Documento {meta.get('document_id', i)}: {doc[:500]}")                                                                                   
                                                                                                                                                                
      return "\n\n".join(docs) 

def tool_query_transactions(db: Session, category: str = None, type: str = None, month: int = None, year: int = None) -> str:
    query = db.query(Transaction)

    if category:
          query = query.join(Category).filter(Category.name.ilike(f"%{category}%"))                                                                             
    if type:                                                                                                                                                  
          query = query.filter(Transaction.type == type) 
    if year:
        try:
            query = query.filter(extract('year', Transaction.transaction_date) == int(year))
        except (ValueError, TypeError):
            pass
    if month:
        try:
            query = query.filter(extract('month', Transaction.transaction_date) == int(month))
        except (ValueError, TypeError):
            pass

    transactions = query.all()

    if not transactions:
        return "No encontré transacciones con esos criterios."

    income = sum(float(t.amount) for t in transactions if t.type.value == "income")
    expenses = sum(float(t.amount) for t in transactions if t.type.value == "expense")
    balance = income - expenses

    result = f"Encontré {len(transactions)} transacciones.\n"
    result += f"Total ingresos: ${income:,.2f}\n"
    result += f"Total gastos: ${expenses:,.2f}\n"
    result += f"Balance: ${balance:,.2f}\n\n"

    for t in transactions[:10]:
        result += f"- {t.transaction_date}: ${float(t.amount):,.2f} ({t.type.value}) - {t.description}\n"

    return result                                                                                                                                   

def tool_get_summary(db:Session, month: int = None, year: int = None) -> str:
      query = db.query(Transaction)  
      if year:
           try:
                query = query.filter(extract('year', Transaction.transaction_date) == int(year))
           except (ValueError, TypeError):
                pass
      if month:
           try:
                query = query.filter(extract('month', Transaction.transaction_date) == int(month))
           except (ValueError, TypeError):
                pass                                                                                                        
      transactions = query.all()                                                                                                                                                               
      if not transactions:                                                                                                                                      
          return "No hay transacciones registradas."                                                                                                            
                                                                                                                                                                
      income = sum(float(t.amount) for t in transactions if t.type.value == "income")                                                                           
      expenses = sum(float(t.amount) for t in transactions if t.type.value == "expense")                                                                        
      balance = income - expenses                                                                                                                               
                                                                                                                                                                
      return f"""Resumen financiero:                                                                                                                            
                - Total ingresos: ${income:,.2f}                                                                                                                              
                - Total gastos: ${expenses:,.2f}                                                                                                                              
                - Balance: ${balance:,.2f}                                                                                                                                    
                - Cantidad de transacciones: {len(transactions)}"""  

def tool_get_max_expense(db: Session, month: int = None, year: int = None) -> str:
     query = db.query(Transaction).filter(Transaction.type == "expense")

     if year: 
          try:
               query = query.filter(extract('year', Transaction.transaction_date) == int(year))
          except (ValueError, TypeError):
               pass
     if month:
          try:
               query = query.filter(extract('month', Transaction.transaction_date) == int(month))
          except (ValueError, TypeError):
               pass
     transaction = query.order_by(Transaction.amount.desc()).first()

     if not transaction:
          return "No encontre gastos con estos criterios"
     return f"El mayor gasto fue: ${float(transaction.amount):,.2f} - {transaction.description} - Fecha: {transaction.transaction_date}" 

def tool_get_max_income(db, month=None, year=None):
     query = db.query(Transaction).filter(Transaction.type == TransactionType.income)

     try:
          if month:
               query = query.filter(extract('month', Transaction.transaction_date) == int(month))
          if year:
               query = query.filter(extract('year', Transaction.transaction_date) == int(year))
     except (ValueError, TypeError):
          pass

     tx = query.order_by(Transaction.amount.desc()).first()
     if not tx:
          return "No se encontraron ingresos."
     return f"El mayor ingreso encontrado fue: ${tx.amount:,.2f} - {tx.description} - Fecha: {tx.transaction_date}"

def tool_get_top_expenses(db: Session, limit: int = 5, month=None, year=None) -> str:
     query = db.query(Transaction).filter(Transaction.type == TransactionType.expense)

     try:
          if month:
               query = query.filter(extract('month', Transaction.transaction_date) == int(month))
          if year:
               query = query.filter(extract('year', Transaction.transaction_date) == int(year))
     except (ValueError, TypeError):
          pass

     transactions = query.order_by(Transaction.amount.desc()).limit(int(limit)).all()

     if not transactions:
          return "No se encontraron gastos con estos criterios"
     
     result = f"Top {len(transactions)} gastos:\n"
     for i, t in enumerate(transactions, 1):
          result += f"{i}. ${float(t.amount):,.2f} - {t.description} - {t.transaction_date}\n"
     return result

def tool_get_category_summary(db: Session, category: str, month=None, year=None) -> str:
     if not category:
          return "Necesito el nombre de una categoria."
     
     query = db.query(Transaction).join(Category).filter(Category.name.ilike(f"%{category}%"))

     try:
          if month:
               query = query.filter(extract('month', Transaction.transaction_date) == int(month))
          if year:
               query = query.filter(extract('year', Transaction.transaction_date) == int(year))
     except (ValueError, TypeError):
          pass
     transactions = query.all()
     if not transactions:
          return f"No se encontraron transacciones para la categoria '{category}'."
     
     total = sum(float(t.amount) for t in transactions)
     average = total / len(transactions)

     result = f"Resumen categoria '{category}':\n"
     result += f"- Total: ${total:,.2f}\n"
     result += f"- Transacciones: {len(transactions)}\n"
     result += f"- Promedio: ${average:,.2f}\n"
     result += f"- Mayor gasto: ${max(float(t.amount) for t in transactions):,.2f}\n\n"
     result += "Detalle:\n"

     for t in transactions[:10]:
          result += f" - {t.transaction_date}: ${float(t.amount):,.2f} - {t.description}\n"
     return result

def tool_list_categories(db: Session) -> str:
     categories = db.query(Category).all()

     if not categories:
          return "No hay categorias registradas."
     
     return "Categorias disponibles:\n" + "\n".join(f"- {c.name}" for c in categories)

def tool_insert_transaction(db: Session, amount: float = None, description: str = None, type: str = None, category: str = None, date_str: str = None) -> str:
    if not amount or not description:
        return "Necesito al menos un monto y una descripcion para poder registrar esta transaccion."
     
    tx_type = type if type in ("income", "expense") else "expense"
    if date_str:
         try:
             tx_date = datetime.strptime(date_str, "%Y-%m-%d").date()
         except ValueError:
              tx_date = date.today()
    else:
         tx_date = date.today()

    category_id = None
    if category:
         cat = db.query(Category).filter(Category.name.ilike(f"%{category}%")).first()
         if cat:
              category_id = cat.id
         else:
              new_cat = Category(name=category)
              db.add(new_cat)
              db.flush()
              category_id = new_cat.id
    tx = Transaction(
         transaction_date=tx_date,
         amount=abs(amount),
         currency="USD",
         type=TransactionType(tx_type),
         description=description,
         category_id=category_id
    )
    db.add(tx)
    db.commit()

    return f"Transaccion registrada: ${abs(amount):,.2f} ({tx_type}) - {description} - Fecha: {tx_date} - Categoria: {category or 'Sin categoria'}"
    

def execute_tool(tool_name: str, params: dict, db: Session) -> str:
     if tool_name == "search_documents":
          return tool_search_documents(params.get("query", ""))
     elif tool_name == "query_transactions":                                                                                                                   
          return tool_query_transactions(db, params.get("category"), params.get("type"), params.get("month"), params.get("year"))                                                                        
     elif tool_name == "get_summary":                                                                                                                          
          return tool_get_summary(db, params.get("month"), params.get("year"))  
     elif tool_name == "get_max_expense":
          return tool_get_max_expense(db, params.get("month"), params.get("year"))                                                                                                                         
     elif tool_name == "list_categories":                                                                                                                      
          return tool_list_categories(db)   
     elif tool_name == "insert_transaction":
          return tool_insert_transaction(db, params.get("amount"), params.get("description"), params.get("type"), params.get("category"), params.get("date_str"))                                                                                                                    
     elif tool_name == "get_max_income":
          return tool_get_max_income(db, params.get("month"), params.get("year"))
     elif tool_name == "get_top_expenses":
          return tool_get_top_expenses(db, params.get("limit", 5), params.get("month"), params.get("year"))
     elif tool_name == "get_category_summary":
          return tool_get_category_summary(db, params.get("category"), params.get("month"), params.get("year"))
     else:                                                                                                                                                     
          return f"Tool '{tool_name}' no encontrada."