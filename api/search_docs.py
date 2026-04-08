import requests
from fastapi import APIRouter
import chromadb

search = APIRouter()
OLLAMA_URL = "http://ollama:11434/api/embed"                                                                                     
CHROMA_CLIENT = chromadb.HttpClient(host='chromadb', port=8000)
COLLECTION = CHROMA_CLIENT.get_or_create_collection(name="documents")

def get_embedding(text: str) -> list:                                                                                                                         
      response = requests.post(                                                                                                                                 
          OLLAMA_URL,                                                                                                                                           
          json={                                                                                                                                                
              "model": "nomic-embed-text",                                                                                                                      
              "input": text                                                                                                          
          }                                                                                                                                                     
      )                                                                                                                                                         
      response.raise_for_status()                                                                                                                               
      return response.json()["embeddings"][0]  


@search.get("/documents/search")
def search_docs(q: str):
    query_docs = get_embedding(q)

    results = COLLECTION.query(
        query_embeddings=[query_docs],
        n_results = 5
    )

    return {
        "query": q,
        "results": [
            {
                "id": results["ids"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i] if results["distances"] else None
            }
            for i in range(len(results["ids"][0]))
        ]
    }