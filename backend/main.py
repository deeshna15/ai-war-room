import os
import json
import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from backend.agents import Agent, compile_war_room_graph
from backend.tools import get_metric_trend, analyze_sentiment, get_release_notes
from backend.data import load_metrics, load_feedback, load_release_notes

app = FastAPI(title="War Room Simulator")

# Mount frontend
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

@app.get("/")
def serve_index():
    return FileResponse(os.path.join(frontend_dir, "index.html"))

@app.get("/api/dashboard-data")
def dashboard_data():
    """Reads telemetry from local physical files to serve the frontend UI"""
    metrics = load_metrics()
    feedback = load_feedback()
    notes = load_release_notes()

    latency = metrics.get('api_latency_p95_ms', [])[-1]
    success = metrics.get('payment_success_rate', [])[-1]
    tickets = metrics.get('support_ticket_volume', [])[-1]

    data = {
        "latency": f"{latency}ms",
        "success": f"{success * 100}%",
        "tickets": tickets,
        "feedback": str(feedback[0].get('comment', 'Failed')) if feedback else '',
        "notes": notes[:150] + "..."
    }
    return data

def create_agents():
    # Define Agents
    analyst_instruction = (
        "You are the Data Analyst Agent in a product launch War Room for 'PurpleMerit'. "
        "Your job is to cleanly analyze metrics objectively using the get_metric_trend tool. "
        "Highlight significant percentage changes or anomalies after Day 10 (Launch). Keep analysis concise."
    )
    analyst_agent = Agent("Data Analyst", analyst_instruction, tools=[get_metric_trend])

    comms_instruction = (
        "You are the Marketing & Comms Agent. You care about user perception and sentiment. "
        "Use analyze_sentiment to read user feedback. Look for recurring themes/complaints."
    )
    comms_agent = Agent("Marketing/Comms", comms_instruction, tools=[analyze_sentiment])

    critic_instruction = (
        "You are the Risk & Critic Agent. Your job is to challenge assumptions and read the fine print. "
        "Use the get_release_notes tool to understand what was changed. Compare technical risks with user/data realities."
    )
    critic_agent = Agent("Risk/Critic", critic_instruction, tools=[get_release_notes])

    pm_instruction = (
        "You are the Product Manager Coordinator. You define success criteria and make the final decision: Proceed, Pause, or Roll Back. "
        "Focus on business impact. Wait for inputs from your team."
    )
    pm_agent = Agent("Product Manager", pm_instruction)

    devops_instruction = "You are the DevOps Lead. Evaluate infrastructure health and technical feasibility of a rollback."
    devops_agent = Agent("DevOps Lead", devops_instruction)
    
    return pm_agent, analyst_agent, comms_agent, critic_agent, devops_agent

@app.get("/api/start")
async def start_war_room(request: Request):
    """Starts the simulation and streams events back via SSE"""
    queue = asyncio.Queue()
    current_loop = asyncio.get_running_loop()

    def callback(sender: str, message: str):
        async def _put():
            await queue.put({"sender": sender, "message": message})
        try:
            asyncio.run_coroutine_threadsafe(_put(), current_loop)
        except Exception as e:
            print("Callback error", e)

    async def run_simulation():
        try:
            pm, analyst, comms, critic, devops = create_agents()
            
            # Run LangGraph multi-agent orchestration in a separate thread
            def run_graph():
                graph = compile_war_room_graph(pm, analyst, comms, critic, devops, callback)
                final_state = graph.invoke({"messages": [], "final_decision": ""})
                return final_state["final_decision"]
                
            final_decision_str = await asyncio.to_thread(run_graph)
            
            try:
                # Validate JSON response
                cleaned = final_decision_str.strip()
                if cleaned.startswith("```json"):
                    cleaned = cleaned[7:-3]
                parsed = json.loads(cleaned)
                
                # Pretty-print final JSON specifically to the terminal required output
                print("\n" + "="*50)
                print("FINAL DECISION PAYLOAD (JSON FORMAT)")
                print("="*50)
                print(json.dumps(parsed, indent=4))
                print("="*50 + "\n")
                
                await queue.put({"sender": "System", "finalData": parsed})
            except Exception as e:
                await queue.put({"sender": "System", "message": f"Failed to parse decision: {str(e)}", "finalRaw": final_decision_str})
                
        except Exception as e:
            await queue.put({"sender": "System", "message": f"Simulation Error: {str(e)}"})
        finally:
            await queue.put({"sender": "System", "message": "[DONE]"})

    asyncio.create_task(run_simulation())

    async def event_generator():
        while True:
            if await request.is_disconnected():
                break
            
            data = await queue.get()
            yield f"data: {json.dumps(data)}\n\n"
            
            if data.get("message") == "[DONE]":
                break

    return StreamingResponse(event_generator(), media_type="text/event-stream")
