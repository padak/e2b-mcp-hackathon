import { NextRequest, NextResponse } from "next/server";
import { forwardToBackend } from "@/lib/e2b";

// Check if we should use E2B backend or mock
const USE_E2B = process.env.E2B_API_KEY && process.env.NODE_ENV === "production";

// In-memory storage for mock simulations
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
    const { market_url, n_runs = 200, question, yes_odds } = body;

    if (!market_url) {
      return NextResponse.json({ error: "market_url is required" }, { status: 400 });
    }

    // Use E2B backend in production
    if (USE_E2B) {
      const response = await forwardToBackend("/simulations", {
        method: "POST",
        body: JSON.stringify({
          market_url,
          question: question || "Unknown market",
          yes_odds: yes_odds || 0.5,
          n_runs,
        }),
      });

      const data = await response.json();
      return NextResponse.json(data);
    }

    // Mock implementation for development
    const simulationId = `sim_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    simulations.set(simulationId, {
      id: simulationId,
      market_url,
      n_runs,
      status: "pending",
      logs: [],
      created_at: new Date(),
    });

    // Start mock simulation
    runMockSimulation(simulationId, market_url, n_runs);

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
  const timestamp = new Date().toLocaleTimeString("en-US", { hour12: false });
  simulation.logs.push({ timestamp, message });
}

async function runMockSimulation(id: string, marketUrl: string, nRuns: number) {
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
      outcomes.push(Math.random() > 0.35 ? 1 : 0);
      if (i % 50 === 0) {
        addLog(simulation, `Monte Carlo run ${i}/${nRuns}`);
      }
      await sleep(15);
    }
    addLog(simulation, "Monte Carlo complete");

    // Calculate results
    const yesCount = outcomes.filter((o) => o === 1).length;
    const simProbability = yesCount / nRuns;
    const marketOdds = 0.65;
    const difference = simProbability - marketOdds;

    const se = Math.sqrt((simProbability * (1 - simProbability)) / nRuns);
    const ci_95: [number, number] = [
      Math.max(0, simProbability - 1.96 * se),
      Math.min(1, simProbability + 1.96 * se),
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
      model_explanation: {
        research_highlights: [
          "Current market sentiment shows strong institutional interest",
          "Recent policy announcements suggest favorable conditions",
          "Historical data indicates 70% correlation with similar events",
          "Expert consensus leans toward positive outcome",
        ],
        agents: {
          "Institutional Investors": {
            count: 50,
            why: "Large market participants with significant influence on price discovery",
            behavior: "Analyze fundamentals and adjust positions based on risk/reward",
            initial_state: "60% bullish based on research indicators",
          },
          "Retail Traders": {
            count: 100,
            why: "Individual market participants who react to news and sentiment",
            behavior: "Follow trends and respond to social signals",
            initial_state: "Mixed sentiment, influenced by recent news",
          },
          "Market Makers": {
            count: 10,
            why: "Provide liquidity and help establish fair market prices",
            behavior: "Balance order flow and manage inventory risk",
            initial_state: "Neutral, adjusting spreads based on volatility",
          },
        },
        simulation_logic: [
          "Each simulation step represents one day of market activity",
          "Agents interact and update their positions based on new information",
          "Random events (news, policy changes) occur with realistic probabilities",
          "After 100 steps, final outcome is determined by majority position",
          "Process repeated 200 times with different random seeds",
        ],
        outcome_interpretation: `The simulation suggests a ${Math.round(simProbability * 100)}% probability of YES outcome, which is ${Math.abs(Math.round(difference * 100))}pp ${difference > 0 ? "higher" : "lower"} than the current market price. This ${Math.abs(difference) > 0.05 ? "significant" : "small"} difference ${Math.abs(difference) > 0.05 ? "may represent" : "likely does not represent"} a trading opportunity.`,
      },
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

export { simulations };
