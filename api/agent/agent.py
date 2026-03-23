import requests
import json
import re
from sqlalchemy.orm import Session
from api.agent.tools import TOOLS, execute_tool

OLLAMA_URL = "http://ollama:11434/api/generate"

def build_system_prompt() -> str:                                                                                                                                                                                                                      
      tools_desc = "\n".join([                                                                                                                                  
          f"- {t['name']}: {t['description']} | Parametros: {t['parameters']}"                                                                                                                  
          for t in TOOLS                                                                                                                                        
      ])                                                                                                                                                        
                                                                                                                                                                
      return f"""Eres un asistente financiero inteligente. Tienes acceso a estas herramientas:

               {tools_desc}

               REGLAS PARA ELEGIR HERRAMIENTA:

               1. Si el usuario pregunta cuánto gastó, cuánto ingresó, balance o saldo de un periodo especifico -> usa "get_summary" con month y year
               2. Si menciona un mes o período específico (ej: "en marzo", "este mes") -> usa "query_transactions" con month y year
               3. Si pregunta por una categoría específica (ej: "gastos de Rent") -> usa "query_transactions" con category
               4. Si pregunta qué categorías tiene -> usa "list_categories"
               5. Si pregunta sobre documentos o facturas -> usa "search_documents"
               6. Si el usuario dice que gastó, pagó, compró o cobró algo -> usa "insert_transaction"
                    - "gasté 500 en el super" -> amount=500, type=expense, description=lo que compró, category=categoría apropiada
                    - "cobré 3000 del cliente" -> amount=3000, type=income, description=lo que describe
                    - Si no menciona fecha, NO envíes date_str (se usará la fecha de hoy)
                    - Palabras clave expense: gasté, pagué, compré, me cobraron
                    - Palabras clave income: cobré, recibí, me pagaron, me transfirieron
               7. Si pregunta cual fue el mayor gasto o la transaccion mas cara -> usa "get_max_expense"
               8. Usa get_max_income cuando pregunten por el mayor ingreso, ingreso más alto o ingreso máximo.
               9. Usa get_top_expenses cuando pregunten por los mayores gastos, más caros o top N gastos. Si mencionan un número (ej: "top 3", "los 5 más caros", "los 5 gastos mas caros de abril en alimentos") pasalo como limit.                                                                                                                                                       
               10. Usa get_category_summary cuando pidan un resumen, detalle o información de una categoría específica. 

               FORMATO DE RESPUESTA - responde SOLO con este JSON:

               {{"tool": "nombre_de_tool", "params": {{"param1": "valor1"}}}}

               Si no necesitas herramienta:
               {{"tool": "none", "params": {{}}, "answer": "tu respuesta directa"}}

               IMPORTANTE: Responde SOLO el JSON, sin texto adicional."""

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
               "model": "qwen2.5:3b",
               "prompt": prompt,
               "stream": False,
               "options": {"temperature": 0.1}
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

                        Responde de forma amigable, cercana y en español a la pregunta: {question}
                        Sé conciso pero cálido. Podés usar emojis ocasionalmente."""

     final_answer = call_llm(final_prompt)
     return {
          "question": question,
          "tool_used": tool_name,
          "tool_params": params,
          "tool_result": tool_result[:500],
          "answer": final_answer
     }