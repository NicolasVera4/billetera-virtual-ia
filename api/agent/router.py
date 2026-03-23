import json 
import requests as req
from fastapi.responses import StreamingResponse
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from connection.database import get_db
from api.agent.agent import run_agent, build_system_prompt, parse_tool_response, call_llm
from api.agent.tools import execute_tool
from pydantic import BaseModel

OLLAMA_URL = "http://ollama:11434/api/generate"
router_agent = APIRouter()

class AgentRequest(BaseModel):
    question: str

@router_agent.post("/agent/stream")
def agent_stream(body: AgentRequest, db: Session = Depends(get_db)):
    def generate():
        system_prompt = build_system_prompt()
        full_prompt = f"{system_prompt}\n\nPregunta del usuario: {body.question}"
        llm_response = call_llm(full_prompt)
        parsed = parse_tool_response(llm_response)

        if parsed.get("tool") == "none":
            answer = parsed.get("answer", llm_response)
            yield f"data: {json.dumps({'type': 'chunk', 'text': answer})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            return
        
        tool_name = parsed.get("tool")
        params = parsed.get("params", {})
        yield f"data: {json.dumps({'type': 'tool', 'tool': tool_name})}\n\n"
        
        tool_result = execute_tool(tool_name, params, db)
        final_prompt = f"""Basándote ÚNICAMENTE en esta información (no inventes datos adicionales):
                           {tool_result}

                           Responde de forma amigable y directa en español a: {body.question}
                           IMPORTANTE:
                           - No uses markdown, asteriscos (*), guiones bajos (_) ni símbolos de formato
                           - Presentá los datos EXACTAMENTE como aparecen arriba, sin modificarlos
                           - Si hay una lista, usá saltos de línea para separarla
                           - Sé conciso y cálido, podés usar emojis"""
        response = req.post(OLLAMA_URL, json={
            "model": "qwen2.5:3b",
            "prompt": final_prompt,
            "stream": True,
            "options": {"temperature": 0.5}
        }, stream=True)

        for line in response.iter_lines():
            if line:
                data = json.loads(line)
                chunk = data.get("response", "")
                if chunk:
                    yield f"data: {json.dumps({'type': 'chunk', 'text': chunk})}\n\n"
                if data.get("done"):
                    yield f"data: {json.dumps({'type': 'done', 'tool': tool_name})}\n\n"
                    break

    return StreamingResponse(generate(), media_type="text/event-stream")

@router_agent.post("/agent")
def agent_endpoint(body: AgentRequest, db: Session = Depends(get_db)):
    result = run_agent(body.question, db)
    return result