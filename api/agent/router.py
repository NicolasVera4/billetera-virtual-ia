import os
import json
from groq import Groq
from fastapi.responses import StreamingResponse
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from connection.database import get_db
from api.agent.agent import run_agent, build_prompt, parse_tool_response, call_llm
from api.agent.tools import execute_tool
from pydantic import BaseModel

groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
GROQ_MODEL = "llama-3.1-8b-instant"
router_agent = APIRouter()

class AgentRequest(BaseModel):
    question: str

@router_agent.post("/agent/stream")
def agent_stream(body: AgentRequest, db: Session = Depends(get_db)):
    def generate():
        accumulated = []
        tools_used = []
        parsed = {}

        for _ in range(2):
            prompt = build_prompt(body.question, accumulated)
            llm_response = call_llm(prompt)
            parsed = parse_tool_response(llm_response)

            tool_name = parsed.get("tool")
            if tool_name == "none" or tool_name in tools_used:
                break

            params = parsed.get("params", {})
            yield f"data: {json.dumps({'type': 'tool', 'tool': tool_name})}\n\n"

            tool_result = execute_tool(tool_name, params, db)
            accumulated.append({"tool": tool_name, "result": tool_result})
            tools_used.append(tool_name)

        if not accumulated:
            answer = parsed.get("answer", "")
            yield f"data: {json.dumps({'type': 'chunk', 'text': answer})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            return

        context_parts = []
        for item in accumulated:
            if item["tool"] == "search_documents":
                context_parts.append(f"Consejos del libro de finanzas:\n{item['result']}")
            else:
                context_parts.append(f"Datos financieros del usuario:\n{item['result']}")

        combined = "\n\n".join(context_parts)
        final_prompt = f"""Basándote ÚNICAMENTE en esta información:

{combined}

Responde de forma amigable y directa en español a: {body.question}
IMPORTANTE:
- No uses markdown, asteriscos (*), guiones bajos (_) ni símbolos de formato
- Si tenes datos financieros reales Y consejos del libro, combinalos en la respuesta
- Presenta los datos EXACTAMENTE como aparecen arriba, sin modificarlos
- Sé conciso y cálido, podés usar emojis"""

        last_tool = tools_used[-1] if tools_used else None
        stream = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": final_prompt}],
            temperature=0.5,
            stream=True
        )
        for chunk in stream:
            text = chunk.choices[0].delta.content or ""
            if text:
                yield f"data: {json.dumps({'type': 'chunk', 'text': text})}\n\n"
        yield f"data: {json.dumps({'type': 'done', 'tool': last_tool})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")

@router_agent.post("/agent")
def agent_endpoint(body: AgentRequest, db: Session = Depends(get_db)):
    result = run_agent(body.question, db)
    return result