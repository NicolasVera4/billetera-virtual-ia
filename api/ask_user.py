import requests
from fastapi import APIRouter
import chromadb

router_rag = APIRouter()

OLLAMA_URL_EMBED = "http://ollama:11434/api/embed"                                                                                                            
OLLAMA_URL_GENERATE = "http://ollama:11434/api/generate"                                                                                                      
CHROMA_CLIENT = chromadb.HttpClient(host='chromadb', port=8000)                                                                                               
COLLECTION = CHROMA_CLIENT.get_or_create_collection(name="documents")

def get_embedding(text: str) -> list:                                                                                                                         
      response = requests.post(                                                                                                                                 
          OLLAMA_URL_EMBED,                                                                                                                                           
          json={                                                                                                                                                
              "model": "nomic-embed-text",                                                                                                                      
              "input": text[:8000]                                                                                                          
          }                                                                                                                                                     
      )                                                                                                                                                         
      response.raise_for_status()                                                                                                                               
      return response.json()["embeddings"][0]  

def search_context(query: str, n_results: int = 3) -> str:
     query_embedding = get_embedding(query)

     results = COLLECTION.query(
          query_embeddings=[query_embedding],
          n_results=n_results,
          include=["documents"]
     )
     documents = results["documents"][0] if results["documents"] else []
     context = "\n\n---\n\n".join(documents)
     return context
def generate_response(prompt:str) -> str:
     response = requests.post(
          OLLAMA_URL_GENERATE,
          json={
               "model": "mistral:7b",
               "prompt": prompt,
               "stream": False
          }
     )
     response.raise_for_status()
     return response.json()["response"]
  
@router_rag.post("/ask")
def ask_question(question: str):
    context = search_context(question)

    if not context:
         return {"answer": "No encontre documentos relevantes para responder."}
    
    prompt = f"""
    Contexto:                                                                                                                                    
    {context}                                                                                                                                                                                                                                                                                                                   
    Pregunta: {question}                                                                                                                                                                                                                                                                                                       
    Responde basándote únicamente en el contexto proporcionado. Si la información no está en el contexto, indica que no tienes esa información.
    """ 

    answer = generate_response(prompt)

    return {
         "question": question,
         "answer": answer,
         "context_used": context[:500] + "..." if len(context) > 500 else context
    }