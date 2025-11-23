import { NextRequest, NextResponse } from "next/server";

// In-memory storage for simulations (ephemeral as per PRD)
interface SimulationData {
  id: string;
  market_url: string;
  n_runs: number;
  status: string;
  progress?: { current: number; total: number };
  result?: Record<string, unknown>;
  error?: string;
  logs: { timestamp: string; message: string }[];
  created_at: Date;
}

const simulations = new Map<string, SimulationData>();

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
      logs: [],
      created_at: new Date(),
    });

    // Start simulation in background
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

function addLog(simulation: SimulationData, message: string) {
  const timestamp = new Date().toLocaleTimeString('en-US', { hour12: false });
  simulation.logs.push({ timestamp, message });
}

async function runSimulation(id: string, marketUrl: string, nRuns: number) {
  const simulation = simulations.get(id);
  if (!simulation) return;

  try {
    // Phase 1: Research
    simulation.status = "research";
    addLog(simulation, "Starting market research...");
    await sleep(1000);
    addLog(simulation, "Fetching current news and data...");
    await sleep(1000);
    addLog(simulation, "Research complete");

    // Phase 2: Generate
    simulation.status = "generate";
    addLog(simulation, "Generating simulation model...");
    await sleep(1500);
    addLog(simulation, "Creating agent definitions...");
    await sleep(1500);
    addLog(simulation, "Model compiled successfully");

    // Phase 3: Calibrate
    simulation.status = "calibrate";
    simulation.progress = { current: 0, total: 50 };
    addLog(simulation, "Starting calibration (50 runs)...");
    for (let i = 1; i <= 50; i++) {
      simulation.progress.current = i;
      if (i % 10 === 0) {
        addLog(simulation, `Calibration run ${i}/50`);
      }
      await sleep(30);
    }
    addLog(simulation, "Calibration complete, threshold determined");

    // Phase 4: Simulate
    simulation.status = "simulate";
    simulation.progress = { current: 0, total: nRuns };
    addLog(simulation, `Starting Monte Carlo (${nRuns} runs)...`);

    const outcomes: number[] = [];
    for (let i = 1; i <= nRuns; i++) {
      simulation.progress.current = i;
      // Simulate outcome (0 or 1)
      outcomes.push(Math.random() > 0.35 ? 1 : 0);
      if (i % 50 === 0) {
        addLog(simulation, `Monte Carlo run ${i}/${nRuns}`);
      }
      await sleep(15);
    }
    addLog(simulation, "Monte Carlo complete");

    // Calculate results
    const yesCount = outcomes.filter(o => o === 1).length;
    const simProbability = yesCount / nRuns;
    const marketOdds = 0.65; // Mock value
    const difference = simProbability - marketOdds;

    // Calculate 95% CI using normal approximation
    const se = Math.sqrt((simProbability * (1 - simProbability)) / nRuns);
    const ci_95: [number, number] = [
      Math.max(0, simProbability - 1.96 * se),
      Math.min(1, simProbability + 1.96 * se)
    ];

    let signal: "BUY_YES" | "BUY_NO" | "HOLD" = "HOLD";
    if (difference > 0.05) signal = "BUY_YES";
    else if (difference < -0.05) signal = "BUY_NO";

    simulation.status = "complete";
    simulation.result = {
      probability: simProbability,
      ci_95: ci_95,
      n_runs: nRuns,
      market_odds: marketOdds,
      difference: difference,
      signal: signal,
      expected_value: difference * 100,
      outcomes: outcomes,
    };
    addLog(simulation, `Simulation complete: ${Math.round(simProbability * 100)}% probability`);
  } catch (error) {
    simulation.status = "error";
    simulation.error = error instanceof Error ? error.message : "Simulation failed";
    addLog(simulation, `Error: ${simulation.error}`);
  }
}

function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// Export simulations map for other routes
export { simulations };
