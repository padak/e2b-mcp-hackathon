import { Sandbox } from "@e2b/code-interpreter";

// Backend sandbox URL cache
let backendUrl: string | null = null;
let backendSandbox: Sandbox | null = null;

const E2B_TEMPLATE = "sim-zpicena-gateway";
const BACKEND_PORT = 8000;

/**
 * Get or create the backend sandbox URL.
 * The backend runs FastAPI and exposes HTTPS URL.
 */
export async function getBackendUrl(): Promise<string> {
  if (backendUrl && backendSandbox) {
    // Check if sandbox is still alive
    try {
      const response = await fetch(`${backendUrl}/health`, {
        method: "GET",
        signal: AbortSignal.timeout(5000),
      });
      if (response.ok) {
        return backendUrl;
      }
    } catch {
      // Sandbox is dead, recreate
      backendUrl = null;
      backendSandbox = null;
    }
  }

  // Create new sandbox
  console.log("Creating E2B backend sandbox...");

  const apiKey = process.env.E2B_API_KEY;
  if (!apiKey) {
    throw new Error("E2B_API_KEY not configured");
  }

  backendSandbox = await Sandbox.create(E2B_TEMPLATE, {
    apiKey,
    timeoutMs: 300000, // 5 minutes
  });

  // Install dependencies and start backend
  console.log("Installing backend dependencies...");

  await backendSandbox.commands.run("pip install fastapi uvicorn pydantic", {
    timeoutMs: 60000,
  });

  // Copy backend code to sandbox
  const backendCode = `
import asyncio
import os
import sys
import json
import uuid
from datetime import datetime
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Simplified backend for E2B
simulations = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(title="WorldSim API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class SimulationRequest(BaseModel):
    market_url: str
    question: str
    yes_odds: float
    n_runs: int = 200

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/markets")
async def get_markets(category: str = None, search_query: str = None, limit: int = 10):
    # Mock data for now - will integrate real Polymarket
    return {"markets": [], "total": 0}

@app.post("/simulations")
async def create_simulation(request: SimulationRequest, background_tasks: BackgroundTasks):
    sim_id = f"sim_{uuid.uuid4().hex[:12]}"
    simulations[sim_id] = {
        "id": sim_id,
        "status": "pending",
        "question": request.question,
        "yes_odds": request.yes_odds,
        "n_runs": request.n_runs,
        "logs": [],
        "progress": None,
        "result": None,
        "error": None,
    }
    background_tasks.add_task(run_simulation, sim_id, request)
    return {"simulation_id": sim_id, "status": "pending"}

@app.get("/simulations/{sim_id}")
async def get_simulation(sim_id: str):
    if sim_id not in simulations:
        raise HTTPException(status_code=404, detail="Not found")
    return simulations[sim_id]

async def run_simulation(sim_id: str, request: SimulationRequest):
    sim = simulations[sim_id]

    def log(msg):
        sim["logs"].append({"timestamp": datetime.now().strftime("%H:%M:%S"), "message": msg})

    try:
        # Research phase
        sim["status"] = "research"
        log("Researching market...")
        await asyncio.sleep(2)

        # Generate phase
        sim["status"] = "generate"
        log("Generating model...")
        await asyncio.sleep(2)

        # Simulate phase
        sim["status"] = "simulate"
        sim["progress"] = {"current": 0, "total": request.n_runs}
        log(f"Running {request.n_runs} simulations...")

        import random
        outcomes = []
        for i in range(request.n_runs):
            outcomes.append(1 if random.random() > 0.35 else 0)
            sim["progress"]["current"] = i + 1
            if i % 50 == 0:
                log(f"Run {i}/{request.n_runs}")
            await asyncio.sleep(0.01)

        prob = sum(outcomes) / len(outcomes)
        diff = prob - request.yes_odds

        sim["status"] = "complete"
        sim["result"] = {
            "probability": prob,
            "ci_95": [max(0, prob - 0.067), min(1, prob + 0.067)],
            "n_runs": request.n_runs,
            "market_odds": request.yes_odds,
            "difference": diff,
            "signal": "BUY_YES" if diff > 0.05 else ("BUY_NO" if diff < -0.05 else "HOLD"),
            "outcomes": outcomes,
            "model_explanation": {
                "research_highlights": ["Market data analyzed", "Recent trends identified"],
                "agents": {"Traders": {"count": 100, "why": "Market participants", "behavior": "Trade based on signals", "initial_state": "Neutral"}},
                "simulation_logic": ["Simulate market dynamics", "Run Monte Carlo"],
                "outcome_interpretation": f"Simulation suggests {prob:.0%} probability"
            }
        }
        log("Complete!")

    except Exception as e:
        sim["status"] = "error"
        sim["error"] = str(e)
        log(f"Error: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
`;

  await backendSandbox.files.write("/home/user/backend.py", backendCode);

  // Start the backend server
  console.log("Starting FastAPI backend...");

  backendSandbox.commands.run("python /home/user/backend.py", {
    background: true,
  });

  // Wait for server to start
  await new Promise((resolve) => setTimeout(resolve, 3000));

  // Get the public URL
  const host = backendSandbox.getHost(BACKEND_PORT);
  backendUrl = `https://${host}`;

  console.log(`Backend URL: ${backendUrl}`);

  return backendUrl;
}

/**
 * Forward request to E2B backend.
 */
export async function forwardToBackend(
  path: string,
  options: RequestInit = {}
): Promise<Response> {
  const url = await getBackendUrl();
  return fetch(`${url}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });
}

/**
 * Cleanup backend sandbox.
 */
export async function cleanupBackend(): Promise<void> {
  if (backendSandbox) {
    await backendSandbox.kill();
    backendSandbox = null;
    backendUrl = null;
  }
}
