"""
FastAPI backend for WorldSim Markets.
Runs in E2B sandbox and orchestrates real simulations.
"""

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

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

# In-memory storage for simulations
simulations = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(title="WorldSim Markets API", lifespan=lifespan)

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


class MarketRequest(BaseModel):
    category: Optional[str] = None
    search_query: Optional[str] = None
    limit: int = 10


@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@app.get("/markets")
async def get_markets(category: str = None, search: str = None, limit: int = 10):
    """Get markets from Polymarket."""
    try:
        from mcp_clients.polymarket import (
            get_markets as fetch_markets,
            get_biggest_movers,
            search_markets,
            select_high_volume_markets,
        )

        markets = []

        if search:
            markets = search_markets(search, limit)
        elif category:
            markets = get_biggest_movers(category, limit)
        else:
            all_markets = fetch_markets(limit=50)
            markets = select_high_volume_markets(all_markets, min_volume=10000)[:limit]

        # Format markets for response
        formatted = []
        for m in markets:
            outcome_prices = m.get("outcomePrices", [])
            if isinstance(outcome_prices, str):
                try:
                    outcome_prices = json.loads(outcome_prices)
                except:
                    outcome_prices = []

            yes_odds = float(outcome_prices[0]) if outcome_prices else 0.5
            volume = float(m.get("volumeNum") or m.get("volume") or 0)

            formatted.append({
                "question": m.get("question", "Unknown"),
                "yes_odds": yes_odds,
                "volume": volume,
                "slug": m.get("slug", ""),
                "conditionId": m.get("conditionId", ""),
            })

        return {"markets": formatted, "total": len(formatted)}

    except Exception as e:
        print(f"Error fetching markets: {e}")
        return {"markets": [], "total": 0, "error": str(e)}


@app.post("/simulations")
async def create_simulation(request: SimulationRequest, background_tasks: BackgroundTasks):
    """Create and start a new simulation."""
    sim_id = f"sim_{int(datetime.now().timestamp() * 1000)}_{uuid.uuid4().hex[:8]}"

    simulations[sim_id] = {
        "id": sim_id,
        "status": "pending",
        "question": request.question,
        "yes_odds": request.yes_odds,
        "n_runs": request.n_runs,
        "market_url": request.market_url,
        "logs": [],
        "progress": None,
        "result": None,
        "error": None,
        "created_at": datetime.now().isoformat(),
    }

    background_tasks.add_task(run_simulation, sim_id, request)

    return {"simulation_id": sim_id, "status": "pending"}


@app.get("/simulations/{sim_id}")
async def get_simulation(sim_id: str):
    """Get simulation status and results."""
    if sim_id not in simulations:
        raise HTTPException(status_code=404, detail="Simulation not found")
    return simulations[sim_id]


async def run_simulation(sim_id: str, request: SimulationRequest):
    """Run the actual simulation pipeline using existing CLI logic."""
    sim = simulations[sim_id]

    # Create a custom log function that updates simulation state
    def update_status(phase: str):
        sim["status"] = phase

    def add_log(msg: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        sim["logs"].append({"timestamp": timestamp, "message": msg})
        print(f"[{sim_id}] {msg}")

    try:
        from sandbox.runner import create_sandbox
        from mcp_clients.perplexity_client import search
        from generator.generator import generate_model_async
        from sandbox.retry import execute_monte_carlo
        from cli import extract_model_info

        add_log(f"Starting simulation for: {request.question[:60]}...")
        add_log(f"Market odds: {request.yes_odds:.0%}")

        # Create sandbox
        update_status("research")
        add_log("Creating E2B sandbox...")
        sbx = await create_sandbox(verbose=False)
        add_log(f"Sandbox created: {sbx.sandbox_id}")

        try:
            # Phase 1: Research (same as CLI)
            add_log("Researching with Perplexity...")
            research_query = f"""
            Provide current data and context for this prediction market question:
            "{request.question}"
            Include recent news, key statistics, expert opinions, and factors that could influence the outcome.
            """
            research = await search(sbx, research_query)
            add_log(f"Research complete: {len(research)} chars")

            # Phase 2: Generate model (same as CLI)
            update_status("generate")
            add_log("Generating simulation model with Claude...")
            code = await generate_model_async(
                question=request.question,
                yes_odds=request.yes_odds,
                research=research
            )
            add_log(f"Model generated: {len(code)} chars")

            # Load fallback model
            fallback_path = os.path.join(
                os.path.dirname(__file__),
                '..',
                'models',
                'economic_shock.py'
            )
            fallback_code = None
            if os.path.exists(fallback_path):
                with open(fallback_path, 'r') as f:
                    fallback_code = f.read()

            # Phase 3 & 4: Execute Monte Carlo (same as CLI)
            update_status("simulate")
            sim["progress"] = {"current": 0, "total": request.n_runs}
            add_log(f"Running Monte Carlo ({request.n_runs} runs)...")

            result = await execute_monte_carlo(
                sbx=sbx,
                code=code,
                n_runs=request.n_runs,
                max_retries=5,
                fallback_code=fallback_code
            )

            if not result.success:
                sim["status"] = "error"
                sim["error"] = result.error
                add_log(f"ERROR: {result.error}")
                return

            add_log(f"Monte Carlo complete: {result.probability:.0%} (±{result.ci_95:.0%})")

            # Calculate results (same as CLI)
            probability = result.probability
            market_odds = request.yes_odds
            difference = probability - market_odds

            # Determine signal
            if difference > 0.05:
                signal = "BUY_YES"
            elif difference < -0.05:
                signal = "BUY_NO"
            else:
                signal = "HOLD"

            # Use CLI's extract_model_info for consistency
            model_info = extract_model_info(code, request.question)

            # Build model explanation from extracted info
            # Better sentence splitting - split on '. ' or '.\n' to avoid breaking mid-sentence
            import re
            sentences = re.split(r'\.\s+', research)
            # Clean up markdown and take first 4 meaningful sentences
            highlights = []
            for s in sentences[:8]:  # Check more to find good ones
                clean = s.strip().replace('**', '').replace('*', '')
                if len(clean) > 30 and len(highlights) < 4:
                    # Add period back and truncate if too long
                    if len(clean) > 200:
                        clean = clean[:197] + "..."
                    highlights.append(clean + ".")

            model_explanation = {
                "research_highlights": highlights or ["Market data analyzed", "Recent trends identified"],
                "agents": {
                    agent["name"]: {
                        "count": agent["count"],
                        "why": f"Represents {agent['name'].lower()} actors",
                        "behavior": "Interacts based on market conditions",
                        "initial_state": f"Initialized from research"
                    }
                    for agent in model_info.get("agents", [])
                } or {"MarketParticipants": {"count": 100, "why": "Market actors", "behavior": "React to signals", "initial_state": "Neutral"}},
                "simulation_logic": [
                    "Each step represents evolving conditions",
                    "Agents interact and update positions",
                    f"Process repeated {request.n_runs} times",
                    "Final outcome from agent decisions"
                ],
                "outcome_interpretation": f"Simulation suggests {probability:.0%} probability, {abs(difference)*100:.0f}pp {'higher' if difference > 0 else 'lower'} than market."
            }

            # Build result
            sim["status"] = "complete"
            sim["result"] = {
                "question": request.question,
                "probability": probability,
                "ci_95": [
                    max(0, probability - result.ci_95),
                    min(1, probability + result.ci_95)
                ],
                "n_runs": result.n_runs,
                "market_odds": market_odds,
                "difference": difference,
                "signal": signal,
                "expected_value": difference * 100,
                "outcomes": result.results,
                "used_fallback": result.used_fallback,
                "model_explanation": model_explanation,
            }

            add_log(f"Simulation complete: {probability:.0%} probability, signal: {signal}")

        finally:
            sbx.kill()
            add_log("Sandbox terminated")

    except Exception as e:
        import traceback
        sim["status"] = "error"
        sim["error"] = str(e)
        add_log(f"EXCEPTION: {str(e)}")
        traceback.print_exc()


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
