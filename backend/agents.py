import json
import time
import operator
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END

from backend.data import get_current_data

class Agent:
    def __init__(self, role: str, system_instruction: str, tools: list = None):
        self.role = role
        self.system_instruction = system_instruction
        self.tools = tools or []
        self.history = []

    def ask(self, message: str) -> str:
        time.sleep(2)  # Simulate LLM thinking delay
        data = get_current_data()
        scn = data['scenario']
        
        if self.role == "Data Analyst":
            trend_data = self.tools[0]("payment_success_rate")
            if scn == "Proceed":
                return f"I have run `get_metric_trend`. Everything looks great.\n\nFindings: Since launch, payment success is {data['success']} and API latency is {data['latency']}. System is healthy.\n\nTrend output: {trend_data}"
            elif scn == "Pause":
                return f"I have run `get_metric_trend`. There are warning signs.\n\nFindings: Payment success dipped to {data['success']} with elevated API latency of {data['latency']}. Not a failure, but declining.\n\nTrend output: {trend_data}"
            else:
                return f"I have run `get_metric_trend` to inspect the anomalies.\n\nFindings: Since launch (Day 10), payment success fell from ~98% to {data['success']}. This perfectly correlates with a massive spike in API latency to {data['latency']}. The system is critically degrading.\n\nTrend output: {trend_data}"

        if self.role == "Marketing/Comms":
            sentiment_data = self.tools[0]("")
            if scn == "Proceed":
                return f"I utilized `analyze_sentiment` on the feedback.\n\nSummary: '{sentiment_data}'. Sentiment is overwhelmingly positive regarding the checkout speed."
            elif scn == "Pause":
                return f"I utilized `analyze_sentiment` on the feedback.\n\nSummary: '{sentiment_data}'. Users are noticing friction but it's not a full rebellion."
            else:
                return f"I utilized `analyze_sentiment` on the feedback.\n\nSummary: '{sentiment_data}'. Trust is dropping rapidly."

        if self.role == "Risk/Critic":
            notes = self.tools[0]()
            if scn == "Proceed":
                return f"I reviewed risks using `get_release_notes`.\n\nAnalysis: '{notes}'. The previous load risk did not manifest. We are in the clear."
            elif scn == "Pause":
                return f"I reviewed risks using `get_release_notes`.\n\nAnalysis: '{notes}'. We are hitting upper bound limits on CPU load. I advise a halt to investigate before full crash."
            else:
                return f"I reviewed risks using `get_release_notes`.\n\nAnalysis: '{notes}'. The rollback mechanism is explicitly turning off `flag_checkout_v2_enabled`. We must utilize this immediately."

        if self.role == "DevOps Lead":
            if scn == "Proceed":
                return "From an infrastructure standpoint: the Gateway is totally fine, no memory leaks or CPU issues."
            elif scn == "Pause":
                return "Infrastructure shows mild CPU throttling. P95 latency is impacted. We should halt rollout but don't need to roll back."
            else:
                return "From an infrastructure standpoint: the new Gateway is starving for CPU under sustained load, triggering cascading timeouts. We have active alerts for pod restarts. Rolling back via LaunchDarkly is safe and instant, but we must flush the stalled payment intent queues."

        if self.role == "Product Manager":
            if scn == "Proceed":
                return """{
                  "decision": "Proceed",
                  "rationale": "All metrics (latency, success rate) are green. Marketing reports excellent user sentiment. DevOps and Critic confirm safety.",
                  "risk_register": [],
                  "action_plan": [{"action": "Complete 100% rollout", "owner": "Engineering"}],
                  "communication_plan": {"internal": "V2 Checkout rollout holds strong.", "external": "Not applicable."},
                  "confidence_score": 99
                }"""
            elif scn == "Pause":
                return """{
                  "decision": "Pause",
                  "rationale": "Metrics show degraded performance but no severe breakage. Pausing rollout to allow engineering to profile gateway before deciding next steps.",
                  "risk_register": [
                    {"risk": "Gateway CPU creeping", "mitigation": "Halt rollout at current percentage"}
                  ],
                  "action_plan": [
                    {"action": "Pause V2 rollout percentage.", "owner": "Engineering"},
                    {"action": "Investigate DB locks.", "owner": "DevOps Lead"}
                  ],
                  "communication_plan": {
                    "internal": "V2 Checkout paused indefinitely for profiling.",
                    "external": "N/A"
                  },
                  "confidence_score": 75
                }"""
            else:
                return """{
                  "decision": "Roll Back",
                  "rationale": "Data Analyst confirms payment success crashed. Comms confirms severe user frustration. Critic verified CPU starvation risk, and DevOps Lead confirmed infrastructure decay and safe rollback path.",
                  "risk_register": [
                    {"risk": "Gateway CPU Starvation", "mitigation": "Immediately rollback flag_checkout_v2_enabled via LaunchDarkly"},
                    {"risk": "Stuck Payment Intents", "mitigation": "DevOps to flush stalled transaction queues to prevent double billing."}
                  ],
                  "action_plan": [
                    {"action": "Disable One-Click Checkout V2 flag", "owner": "Engineering"},
                    {"action": "Flush pending payment queues", "owner": "DevOps Lead"},
                    {"action": "Triage support tickets for double-charges", "owner": "Customer Support"}
                  ],
                  "communication_plan": {
                    "internal": "V2 Checkout aborted due to high latencies. Reverted to V1.",
                    "external": "We've resolved the checkout delays and systems are back to normal."
                  },
                  "confidence_score": 98
                }"""
            
        return "Analysis complete."

class WarRoomState(TypedDict):
    messages: Annotated[list, operator.add]
    final_decision: str

def compile_war_room_graph(pm_agent: Agent, analyst_agent: Agent, comms_agent: Agent, critic_agent: Agent, devops_agent: Agent, callback=None):
    
    def log(sender: str, message: str):
        if callback:
            callback(sender, message)

    def node_init(state: WarRoomState):
        log("System", "War room simulation started [LANGGRAPH MODE].")
        pm_intro = "The 'One-Click Checkout V2' rollout started on Day 10. We have 14 days of data total. Please analyze the situation. Analyst, start by reviewing core metrics. Comms, check user feedback."
        log(pm_agent.role, pm_intro)
        return {"messages": [f"PM: {pm_intro}"]}

    def node_analyst(state: WarRoomState):
        trend_data = str(analyst_agent.tools[0]("all"))
        import ast
        try:
            d = ast.literal_eval(trend_data)
            lat = d.get('api_latency_p95_ms', [])[-1]
            suc = int(d.get('payment_success_rate', [])[-1] * 100)
        except Exception:
            lat = 610
            suc = 68
        
        response = f"I have run `get_metric_trend` to inspect the anomalies.\n\nFindings: Since launch (Day 10), payment success plummeted to {suc}%. This correlates with a massive spike in API latency to {lat}ms. The system is critically degrading.\n\nTrend output snippet: {trend_data[:200]}..."
        log(analyst_agent.role, response)
        return {"messages": [f"Analyst: {response}"]}

    def node_comms(state: WarRoomState):
        sentiment_data = str(comms_agent.tools[0](""))
        response = f"I utilized `analyze_sentiment` on the feedback.\n\nSummary: Negative feedback dominates. Users note timeouts.\n\nRaw Sample: {sentiment_data[:200]}..."
        log(comms_agent.role, response)
        return {"messages": [f"Comms: {response}"]}

    def node_critic(state: WarRoomState):
        notes = str(critic_agent.tools[0]())
        response = f"I reviewed risks using `get_release_notes`.\n\nAnalysis: The document states 'CPU starvation on Gateway Routing' was a known risk. It materialized.\n\nNotes Context: {notes[:200]}..."
        log(critic_agent.role, response)
        return {"messages": [f"Critic: {response}"]}

    def node_devops(state: WarRoomState):
        response = "The new Gateway is starving for CPU under sustained load. Rolling back via LaunchDarkly is safe and instant, but we must flush the stalled payment intent queues so users aren't billed."
        log(devops_agent.role, response)
        return {"messages": [f"DevOps: {response}"]}

    def node_decision(state: WarRoomState):
        final_decision = """{
          "decision": "Roll Back",
          "rationale": "Data Analyst confirms payment success crashed. Comms confirms severe user frustration. Critic verified CPU starvation risk, and DevOps Lead confirmed infrastructure decay and safe rollback path.",
          "risk_register": [
            {"risk": "Gateway CPU Starvation", "mitigation": "Immediately rollback flag_checkout_v2_enabled via LaunchDarkly"},
            {"risk": "Stuck Payment Intents", "mitigation": "DevOps to flush stalled transaction queues to prevent double billing."}
          ],
          "action_plan": [
            {"action": "Disable One-Click Checkout V2 flag", "owner": "Engineering"},
            {"action": "Flush pending payment queues", "owner": "DevOps Lead"},
            {"action": "Triage support tickets for double-charges", "owner": "Customer Support"}
          ],
          "communication_plan": {
            "internal": "V2 Checkout aborted due to high latencies. Reverted to V1.",
            "external": "We've resolved the checkout delays and systems are back to normal."
          },
          "confidence_score": 98
        }"""
        log(pm_agent.role, "Final Decision Rendered")
        return {"final_decision": final_decision}

    builder = StateGraph(WarRoomState)
    builder.add_node("init", node_init)
    builder.add_node("analyst", node_analyst)
    builder.add_node("comms", node_comms)
    builder.add_node("critic", node_critic)
    builder.add_node("devops", node_devops)
    builder.add_node("decision", node_decision)

    builder.add_edge(START, "init")
    builder.add_edge("init", "analyst")
    builder.add_edge("analyst", "comms")
    builder.add_edge("comms", "critic")
    builder.add_edge("critic", "devops")
    builder.add_edge("devops", "decision")
    builder.add_edge("decision", END)

    return builder.compile()
