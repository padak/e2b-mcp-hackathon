#!/usr/bin/env python3
"""
FastAPI Backend for WorldSim Markets

Runs in E2B sandbox and exposes HTTPS API for Vercel frontend.
"""

import asyncio
import os
import sys
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.sandbox.runner import create_sandbox
from src.mcp_clients.perplexity_client import search
from src.generator.generator import generate_model_async
from src.sandbox.retry import execute_monte_carlo
from src.mcp_clients.polymarket import (
    get_markets, get_biggest_movers, search_markets,
    select_high_volume_markets
)

# In-memory storage for simulations
simulations: dict = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("WorldSim Backend starting...")
    yield
    # Shutdown
    print("WorldSim Backend shutting down...")

app = FastAPI(
    title="WorldSim Markets API",
    description="Backend API for Monte Carlo market simulations",
    version="1.0.0",
    lifespan=lifespan
)

# CORS for Vercel frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Models ---

class SimulationRequest(BaseModel):
    market_url: str
    question: str
    yes_odds: float
    n_runs: int = 200

class MarketQuery(BaseModel):
    category: Optional[str] = None
    search: Optional[str] = None
    limit: int = 10

# --- Helpers ---

def extract_model_explanation(code: str, research: str, question: str) -> dict:
    """Extract explanation from generated code or create default."""
    import re

    explanation = {
        "research_highlights": [],
        "agents": {},
        "simulation_logic": [],
        "outcome_interpretation": ""
    }

    # Extract research highlights (first 4 sentences)
    sentences = research.split('.')[:4]
    explanation["research_highlights"] = [s.strip() + '.' for s in sentences if s.strip()]

    # Extract AGENT_CONFIG from code
    config_match = re.search(r'AGENT_CONFIG\s*=\s*\{([^}]+)\}', code)
    if config_match:
        config_str = config_match.group(1)
        for line in config_str.split(','):
            match = re.search(r'(\w+):\s*(\d+)', line)
            if match:
                agent_name = match.group(1)
                count = int(match.group(2))
                explanation["agents"][agent_name] = {
                    "count": count,
                    "why": f"Agent type representing {agent_name.lower()} behavior",
                    "behavior": "Interacts with other agents based on model rules",
                    "initial_state": "Initialized from research data"
                }

    # Default simulation logic
    explanation["simulation_logic"] = [
        "Each simulation step represents one time period",
        "Agents interact and update their states",
        "Random events occur with calibrated probabilities",
        "After all steps, outcome is determined",
        f"Process repeated {200} times with different seeds"
    ]

    return explanation

# --- Endpoints ---

@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.get("/markets")
async def get_markets_endpoint(
    category: Optional[str] = None,
    search_query: Optional[str] = None,
    limit: int = 10
):
    """Get markets from Polymarket."""
    try:
        if search_query:
            markets = search_markets(search_query, limit)
        elif category and category != "all":
            markets = get_biggest_movers(category, limit)
        else:
            all_markets = get_markets(limit=50)
            markets = select_high_volume_markets(all_markets, min_volume=10000)[:limit]

        # Format markets for frontend
        result = []
        for m in markets:
            outcome_prices = m.get("outcomePrices", [])
            if isinstance(outcome_prices, str):
                try:
                    outcome_prices = json.loads(outcome_prices)
                except:
                    outcome_prices = []

            yes_odds = float(outcome_prices[0]) if outcome_prices else 0.5
            volume = float(m.get("volumeNum") or m.get("volume") or 0)

            result.append({
                "slug": m.get("slug", ""),
                "question": m.get("question", "Unknown"),
                "yes_odds": yes_odds,
                "volume": volume,
                "end_date": m.get("endDate", ""),
                "category": category or "all"
            })

        return {"markets": result, "total": len(result)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/simulations")
async def create_simulation(request: SimulationRequest, background_tasks: BackgroundTasks):
    """Start a new simulation."""
    simulation_id = f"sim_{uuid.uuid4().hex[:12]}"

    simulations[simulation_id] = {
        "id": simulation_id,
        "status": "pending",
        "question": request.question,
        "yes_odds": request.yes_odds,
        "n_runs": request.n_runs,
        "logs": [],
        "progress": None,
        "result": None,
        "error": None,
        "created_at": datetime.now().isoformat()
    }

    # Run simulation in background
    background_tasks.add_task(
        run_simulation,
        simulation_id,
        request.question,
        request.yes_odds,
        request.n_runs
    )

    return {"simulation_id": simulation_id, "status": "pending"}

@app.get("/simulations/{simulation_id}")
async def get_simulation(simulation_id: str):
    """Get simulation status and results."""
    if simulation_id not in simulations:
        raise HTTPException(status_code=404, detail="Simulation not found")

    sim = simulations[simulation_id]
    return {
        "id": sim["id"],
        "status": sim["status"],
        "progress": sim["progress"],
        "logs": sim["logs"][-20:],  # Last 20 logs
        "result": sim["result"],
        "error": sim["error"]
    }

async def run_simulation(sim_id: str, question: str, yes_odds: float, n_runs: int):
    """Run the actual simulation."""
    sim = simulations[sim_id]

    def add_log(message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        sim["logs"].append({"timestamp": timestamp, "message": message})

    try:
        # Phase 1: Create sandbox
        sim["status"] = "research"
        add_log("Creating E2B sandbox...")
        sbx = await create_sandbox()
        add_log(f"Sandbox ready: {sbx.sandbox_id}")

        try:
            # Phase 2: Research
            add_log("Researching with Perplexity...")
            research_query = f"""
            Provide current data and context for this prediction market question:
            "{question}"
            Include recent news, key statistics, expert opinions, and factors that could influence the outcome.
            """
            research = await search(sbx, research_query)
            add_log(f"Research complete: {len(research)} chars")

            # Phase 3: Generate model
            sim["status"] = "generate"
            add_log("Generating simulation model with Claude...")
            code = await generate_model_async(
                question=question,
                yes_odds=yes_odds,
                research=research
            )
            add_log(f"Model generated: {len(code)} chars")

            # Load fallback model
            fallback_path = os.path.join(
                os.path.dirname(__file__),
                'src', 'models', 'economic_shock.py'
            )
            fallback_code = None
            if os.path.exists(fallback_path):
                with open(fallback_path, 'r') as f:
                    fallback_code = f.read()

            # Phase 4: Execute Monte Carlo
            sim["status"] = "simulate"
            sim["progress"] = {"current": 0, "total": n_runs}
            add_log(f"Running Monte Carlo ({n_runs} runs)...")

            # Progress callback to update simulation state
            def update_progress(current: int, total: int):
                sim["progress"] = {"current": current, "total": total}

            result = await execute_monte_carlo(
                sbx=sbx,
                code=code,
                n_runs=n_runs,
                max_retries=5,
                fallback_code=fallback_code,
                progress_callback=update_progress
            )

            if not result.success:
                raise Exception(result.error)

            add_log(f"Monte Carlo complete: {result.probability:.0%}")

            # Calculate signal
            difference = result.probability - yes_odds
            if difference > 0.05:
                signal = "BUY_YES"
            elif difference < -0.05:
                signal = "BUY_NO"
            else:
                signal = "HOLD"

            # Extract model explanation
            explanation = extract_model_explanation(code, research, question)
            explanation["outcome_interpretation"] = (
                f"The simulation suggests a {result.probability:.0%} probability, "
                f"which is {abs(difference)*100:.1f}pp {'higher' if difference > 0 else 'lower'} "
                f"than the market price of {yes_odds:.0%}."
            )

            # Complete
            sim["status"] = "complete"
            sim["progress"] = {"current": n_runs, "total": n_runs}
            sim["result"] = {
                "probability": result.probability,
                "ci_95": [result.probability - result.ci_95, result.probability + result.ci_95],
                "n_runs": result.n_runs,
                "market_odds": yes_odds,
                "difference": difference,
                "signal": signal,
                "expected_value": difference * 100,
                "outcomes": result.results,
                "used_fallback": result.used_fallback,
                "model_explanation": explanation
            }
            add_log("Simulation complete!")

        finally:
            sbx.kill()
            add_log("Sandbox terminated")

    except Exception as e:
        sim["status"] = "error"
        sim["error"] = str(e)
        add_log(f"Error: {str(e)}")

# --- Main ---

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
