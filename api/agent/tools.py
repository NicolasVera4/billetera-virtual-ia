from sqlalchemy.orm import Session
from connection.database import get_db
from connection.models import Transaction, Category
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
          "parameters": ["category", "type"]                                                                                                                    
      },                                                                                                                                                        
      {                                                                                                                                                         
          "name": "get_summary",                                                                                                                                
          "description": "Obtiene resumen financiero con totales. Usar cuando piden balance, totales o resumen general.",                                       
          "parameters": []                                                                                                                                      
      },                                                                                                                                                        
      {                                                                                                                                                         
          "name": "list_categories",                                                                                                                            
          "description": "Lista todas las categorías disponibles. Usar cuando preguntan qué categorías existen.",                                               
          "parameters": []                                                                                                                                      
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

def tool_query_transactions(db: Session, category: str = None, type: str = None) -> str:
    query = db.query(Transaction)

    if category:
          query = query.join(Category).filter(Category.name.ilike(f"%{category}%"))                                                                             
    if type:                                                                                                                                                  
          query = query.filter(Transaction.type == type)                                                                                                        
                                                                                                                                                                
    transactions = query.all()                                                                                                                                
                                                                                                                                                                
    if not transactions:                                                                                                                                      
          return "No encontré transacciones con esos criterios."                                                                                                
                                                                                                                                                                
    total = sum(float(t.amount) for t in transactions)                                                                                                        
    result = f"Encontré {len(transactions)} transacciones. Total: ${total:,.2f}\n\n"                                                                          
                                                                                                                                                                
    for t in transactions[:10]:  # Limitar a 10                                                                                                               
          result += f"- {t.transaction_date}: ${float(t.amount):,.2f} - {t.description}\n"                                                                      
                                                                                                                                                                
    return result                                                                                                                                   

def tool_get_summary(db:Session) -> str:
      transactions = db.query(Transaction).all()                                                                                                                
                                                                                                                                                                
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

def tool_list_categories(db: Session) -> str:
     categories = db.query(Category).all()

     if not categories:
          return "No hay categorias registradas."
     
     return "Categorias disponibles:\n" + "\n".join(f"- {c.name}" for c in categories)

def execute_tool(tool_name: str, params: dict, db: Session) -> str:
     if tool_name == "search_documents":
          return tool_search_documents(params.get("query", ""))
     elif tool_name == "query_transactions":                                                                                                                   
          return tool_query_transactions(db, params.get("category"), params.get("type"))                                                                        
     elif tool_name == "get_summary":                                                                                                                          
          return tool_get_summary(db)                                                                                                                           
     elif tool_name == "list_categories":                                                                                                                      
          return tool_list_categories(db)                                                                                                                       
     else:                                                                                                                                                     
          return f"Tool '{tool_name}' no encontrada."