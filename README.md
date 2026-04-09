# 🟣 PurpleMerit | Multi-Agent War Room Simulator

This repository contains a dynamic, multi-agent simulation of a cross-functional product launch "War Room." The system evaluates simulated post-launch data (e.g., API latencies, support ticket volumes, and payment success rates) alongside qualitative user feedback to autonomously render a tactical Launch Decision ("Proceed," "Pause," or "Roll Back").

## Features
- **Dynamic Scenario Generation**: Every time the simulation runs, a unique launch context is generated across a randomized spectrum of healthy to critical parameters.
- **5-Agent Architecture**: Includes autonomous personas—Product Manager, Data Analyst, Marketing/Comms, Risk/Critic, and DevOps Lead—collaborating logically.
- **Real-Time UI**: A premium, "glassmorphism" styled web interface offering a dashboard and an active trace channel streamed via Server-Sent Events (SSE).
- **Offline Deterministic Mode**: An implementation that perfectly functions offline, requiring zero LLM inference credits to avoid external rate-limiting bottlenecks.

---

## 🛠️ Setup Instructions

### Prerequisites
- Python 3.9+
- A modern web browser 

### Installation
1. Clone or navigate to the repository directory.
2. Install the necessary Python packages using `pip`:

```bash
pip install -r requirements.txt
```
*(The required packages include FastAPI, Uvicorn, and other standard networking utilities).*

---

## 🔑 Environment Variables Required

Currently, the war room has been upgraded to a **Dynamic Offline Mode** to ensure 100% reliable execution during demos without hitting `429 Too Many Requests` or API billing blocks from OpenAI/OpenRouter.

Because of this, **no environment variables are specifically required** to successfully run the simulation. 
*(If you wish to fork and attach a live LLM, you may supply API keys via a `.env` file.)*

---

## 🚀 How to Run End-to-End

This simulation features a coupled FastAPI Backend and Vanilla HTML/CSS Frontend. To run the system:

1. **Start the Uvicorn Server**
From the root directory (`c:\ai-war-room`), execute the following command:
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

2. **Open the Dashboard**
Navigate to [http://localhost:8000](http://localhost:8000) in your web browser. 
As soon as the page mounts, it dynamically requests current launch telemetry and populates the dashboard (Green = Healthy, Red = Critical).

3. **Initialize the Protocol**
Click the **"Initialize Protocol"** button in the top right corner. The agent swarm will begin streaming logic via the Comms Channel right beside the data panel. 
Upon conclusion, the Product Manager will deliver the structured JSON decision containing the `rationale`, `action_plan`, and `risk_register` via a modal overlay.

---

## 💻 Example Commands to Reproduce Output

Because the simulated reality is random, reproducing different War Room output sets relies on simple repetition:

* **Generate Novel Dashboards**: Simply refresh your browser tab (`F5` or `Ctrl+R`). The telemetry API will roll a new state.
* **Run Simulation on Specific State**: After refreshing until you see a "Spiking Latency" dashboard, click "Initialize Protocol." The agents will adapt their findings and recommend a "Roll Back." Refresh until you see a healthy dashboard, and the agents will determine to "Proceed" with 99% confidence.
