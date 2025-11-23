import { NextRequest, NextResponse } from "next/server";

// In-memory storage for simulations (ephemeral as per PRD)
const simulations = new Map<string, {
  id: string;
  market_url: string;
  n_runs: number;
  status: string;
  progress?: { current: number; total: number };
  result?: Record<string, unknown>;
  error?: string;
  created_at: Date;
}>();

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { market_url, n_runs = 200 } = body;

    if (!market_url) {
      return NextResponse.json({ error: "market_url is required" }, { status: 400 });
    }

    // Generate simulation ID
    const simulationId = `sim_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    // Store simulation
    simulations.set(simulationId, {
      id: simulationId,
      market_url,
      n_runs,
      status: "pending",
      created_at: new Date(),
    });

    // Start simulation in background (we'll implement E2B backend later)
    // For now, trigger a mock simulation process
    runSimulation(simulationId, market_url, n_runs);

    return NextResponse.json({
      simulation_id: simulationId,
      status: "pending",
    });
  } catch (error) {
    console.error("Error creating simulation:", error);
    return NextResponse.json({ error: "Failed to create simulation" }, { status: 500 });
  }
}

async function runSimulation(id: string, marketUrl: string, nRuns: number) {
  const simulation = simulations.get(id);
  if (!simulation) return;

  try {
    // Phase 1: Research
    simulation.status = "research";
    await sleep(2000);

    // Phase 2: Generate
    simulation.status = "generate";
    await sleep(3000);

    // Phase 3: Calibrate
    simulation.status = "calibrate";
    simulation.progress = { current: 0, total: 50 };
    for (let i = 1; i <= 50; i++) {
      simulation.progress.current = i;
      await sleep(50);
    }

    // Phase 4: Simulate
    simulation.status = "simulate";
    simulation.progress = { current: 0, total: nRuns };
    for (let i = 1; i <= nRuns; i++) {
      simulation.progress.current = i;
      await sleep(25);
    }

    // Complete with mock result
    // Extract market odds from URL for comparison
    const marketOdds = 0.65; // Mock value, will be fetched in real implementation
    const simProbability = 0.58 + Math.random() * 0.14; // Random between 0.58-0.72
    const difference = simProbability - marketOdds;

    let signal: "BUY_YES" | "BUY_NO" | "HOLD" = "HOLD";
    if (difference > 0.05) signal = "BUY_YES";
    else if (difference < -0.05) signal = "BUY_NO";

    simulation.status = "complete";
    simulation.result = {
      probability: simProbability,
      ci_95: [simProbability - 0.067, simProbability + 0.067],
      n_runs: nRuns,
      market_odds: marketOdds,
      difference: difference,
      signal: signal,
      expected_value: difference * 100,
    };
  } catch (error) {
    simulation.status = "error";
    simulation.error = error instanceof Error ? error.message : "Simulation failed";
  }
}

function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// Export simulations map for other routes
export { simulations };
