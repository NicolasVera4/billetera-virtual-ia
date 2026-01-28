import requests
import json
import re
from sqlalchemy.orm import Session
from api.agent.tools import TOOLS, execute_tool

OLLAMA_URL = "http://ollama:11434/api/generate"

def build_system_prompt() -> str:                                                                                                                                                                                                                      
      tools_desc = "\n".join([                                                                                                                                  
          f"- {t['name']}: {t['description']}"                                                                                                                  
          for t in TOOLS                                                                                                                                        
      ])                                                                                                                                                        
                                                                                                                                                                
      return f"""Eres un asistente financiero. Tienes acceso a estas herramientas:                                                                              
                                                                                                                                                                
                {tools_desc}                                                                                                                                                  
                                                                                                                                                                                
                Para responder, SIEMPRE debes:                                                                                                                                
                1. Analizar qué herramienta necesitas                                                                                                                         
                2. Responder en formato JSON exacto:                                                                                                                          
                                                                                                                                                                                
                {{"tool": "nombre_de_tool", "params": {{"param1": "valor1"}}}}                                                                                                
                                                                                                                                                                                
                Si no necesitas herramienta, responde:                                                                                                                        
                {{"tool": "none", "params": {{}}, "answer": "tu respuesta directa"}}                                                                                          
                                                                                                                                                                                
                IMPORTANTE: Responde SOLO el JSON, nada más.""" 

def parse_tool_response(response: str) -> dict:
     try:
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
             return json.loads(json_match.group())
     except json.JSONDecodeError:
          pass
     return{"tool": "none", "params": {}, "answer": response}

def call_llm(prompt: str) -> str:
     response = requests.post(
          OLLAMA_URL,
          json={
               "model": "mistral:7b",
               "prompt": prompt,
               "stream": False
          }
     )
     response.raise_for_status()
     return response.json()["response"]

def run_agent(question: str, db: Session) -> dict:
     system_prompt = build_system_prompt()
     full_prompt = f"{system_prompt}\n\nPregunta del usuario: {question}"

     llm_response = call_llm(full_prompt)
     parsed = parse_tool_response(llm_response)

     if parsed.get("tool") == "none":
          return {
               "question": question,
               "tool_used": None,
               "answer": parsed.get("answer", llm_response)
          }
     tool_name = parsed.get("tool")
     params = parsed.get("params", {})
     tool_result = execute_tool(tool_name, params, db)
     
     final_prompt = f"""Basándote en esta información:                                                                                                         
                       {tool_result}                                                                                                                                                                                                                                                                                                               
                        Responde de forma clara y concisa a la pregunta: {question}"""

     final_answer = call_llm(final_prompt)
     return {
          "question": question,
          "tool_used": tool_name,
          "tool_params": params,
          "tool_result": tool_result[:500],
          "answer": final_answer
     }