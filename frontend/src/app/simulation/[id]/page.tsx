"use client";

import { useEffect, useState, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import dynamic from "next/dynamic";
import { SimulationStatus, LogEntry, ModelExplanation } from "@/types";
import ModelExplainer from "@/components/ModelExplainer";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

const PHASE_LABELS: Record<string, string> = {
  pending: "Starting...",
  research: "Researching market context",
  generate: "Generating simulation model",
  calibrate: "Calibrating threshold",
  simulate: "Running Monte Carlo",
  complete: "Complete",
  error: "Error",
};

interface ExtendedSimulationStatus extends SimulationStatus {
  logs?: LogEntry[];
}

export default function SimulationPage() {
  const params = useParams();
  const router = useRouter();
  const [simulation, setSimulation] = useState<ExtendedSimulationStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showChart, setShowChart] = useState(false);
  const logContainerRef = useRef<HTMLDivElement>(null);

  const id = params.id as string;

  useEffect(() => {
    if (!id) return;

    const pollStatus = async () => {
      try {
        const res = await fetch(`/api/simulations/${id}`);
        if (!res.ok) {
          setError("Simulation not found");
          return;
        }
        const data: ExtendedSimulationStatus = await res.json();
        setSimulation(data);

        // Auto-scroll logs
        if (logContainerRef.current) {
          logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
        }

        // Continue polling if not complete
        if (data.status !== "complete" && data.status !== "error") {
          setTimeout(pollStatus, 300);
        }
      } catch {
        setError("Failed to fetch simulation status");
      }
    };

    pollStatus();
  }, [id]);

  const downloadResult = () => {
    if (!simulation?.result) return;
    const blob = new Blob([JSON.stringify(simulation.result, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `simulation-${id}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const downloadModel = () => {
    if (!simulation?.result?.model_code) return;
    const blob = new Blob([simulation.result.model_code], { type: "text/x-python" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `model-${id}.py`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (error) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center p-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md">
          <h2 className="text-red-700 font-semibold mb-2">Error</h2>
          <p className="text-red-600">{error}</p>
          <button
            onClick={() => router.push("/")}
            className="mt-4 text-blue-600 hover:underline"
          >
            Back to Home
          </button>
        </div>
      </div>
    );
  }

  if (!simulation) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-pulse text-gray-500">Loading...</div>
      </div>
    );
  }

  const isComplete = simulation.status === "complete";
  const isError = simulation.status === "error";
  const result = simulation.result;

  // Calculate EV (Expected Value per $100 bet)
  const calculateEV = () => {
    if (!result) return null;
    const prob = result.probability;
    const marketOdds = result.market_odds;

    // EV for betting YES
    const evYes = (prob * (100 / marketOdds)) - 100;
    // EV for betting NO
    const evNo = ((1 - prob) * (100 / (1 - marketOdds))) - 100;

    return {
      yes: Math.round(evYes),
      no: Math.round(evNo),
      recommended: evYes > evNo ? "YES" : "NO",
      value: Math.round(Math.max(evYes, evNo)),
    };
  };

  const ev = calculateEV();

  // Prepare bar chart data with market odds line
  const barChartData = result?.outcomes ? (() => {
    const outcomes = result.outcomes as number[];
    const yesCount = outcomes.filter(o => o === 1).length;
    const noCount = outcomes.length - yesCount;
    const total = outcomes.length;
    const yesPercent = Math.round((yesCount / total) * 100);
    const noPercent = 100 - yesPercent;

    return [
      {
        type: "bar" as const,
        x: ["No", "Yes"],
        y: [noCount, yesCount],
        text: [`${noPercent}%`, `${yesPercent}%`],
        textposition: "inside" as const,
        textfont: { color: "white", size: 14 },
        marker: {
          color: ["#ef4444", "#22c55e"],
        },
        name: "Results",
      },
    ];
  })() : [];

  // Market odds reference line for bar chart
  const marketOddsLine = result ? {
    type: "scatter" as const,
    x: ["No", "Yes"],
    y: [result.n_runs * (1 - result.market_odds), result.n_runs * result.market_odds],
    mode: "lines" as const,
    line: { color: "#3b82f6", width: 2, dash: "dash" as const },
    name: "Market Odds",
  } : null;

  // Prepare convergence chart data
  const convergenceData = result?.outcomes ? (() => {
    const outcomes = result.outcomes as number[];
    const runningProb: number[] = [];
    const runningCI: number[] = [];
    let sum = 0;

    for (let i = 0; i < outcomes.length; i++) {
      sum += outcomes[i];
      const p = sum / (i + 1);
      runningProb.push(p * 100);
      // 95% CI using normal approximation
      const ci = 1.96 * Math.sqrt((p * (1 - p)) / (i + 1)) * 100;
      runningCI.push(ci);
    }

    const runs = Array.from({ length: outcomes.length }, (_, i) => i + 1);

    return {
      probability: {
        type: "scatter" as const,
        x: runs,
        y: runningProb,
        mode: "lines" as const,
        line: { color: "#22c55e", width: 2 },
        name: "Probability",
      },
      upperBound: {
        type: "scatter" as const,
        x: runs,
        y: runningProb.map((p, i) => Math.min(100, p + runningCI[i])),
        mode: "lines" as const,
        line: { width: 0 },
        showlegend: false,
        hoverinfo: "skip" as const,
      },
      lowerBound: {
        type: "scatter" as const,
        x: runs,
        y: runningProb.map((p, i) => Math.max(0, p - runningCI[i])),
        mode: "lines" as const,
        line: { width: 0 },
        fill: "tonexty" as const,
        fillcolor: "rgba(34, 197, 94, 0.2)",
        showlegend: false,
        hoverinfo: "skip" as const,
      },
      marketLine: {
        type: "scatter" as const,
        x: [1, outcomes.length],
        y: [result.market_odds * 100, result.market_odds * 100],
        mode: "lines" as const,
        line: { color: "#3b82f6", width: 2, dash: "dash" as const },
        name: "Market Odds",
      },
    };
  })() : null;

  return (
    <div className="min-h-screen flex flex-col items-center p-8">
      <div className="w-full max-w-4xl">
        <h1 className="text-3xl font-bold text-center mb-8">
          {isComplete ? "Results" : "Simulating..."}
        </h1>

        {!isComplete && !isError && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            {/* Progress Steps */}
            <div className="space-y-4 mb-6">
              {["research", "generate", "calibrate", "simulate"].map((phase) => {
                const phases = ["pending", "research", "generate", "calibrate", "simulate", "complete"];
                const currentIndex = phases.indexOf(simulation.status);
                const phaseIndex = phases.indexOf(phase);
                const isActive = simulation.status === phase;
                const isDone = currentIndex > phaseIndex;

                return (
                  <div key={phase} className="flex items-center gap-3">
                    <div
                      className={`w-6 h-6 rounded-full flex items-center justify-center text-sm ${
                        isDone
                          ? "bg-green-500 text-white"
                          : isActive
                          ? "bg-blue-500 text-white animate-pulse"
                          : "bg-gray-200 text-gray-500"
                      }`}
                    >
                      {isDone ? "✓" : isActive ? "..." : "○"}
                    </div>
                    <span
                      className={`${
                        isActive ? "text-blue-600 font-medium" : isDone ? "text-gray-600" : "text-gray-400"
                      }`}
                    >
                      {PHASE_LABELS[phase]}
                    </span>
                    {isActive && simulation.progress && (
                      <span className="text-sm text-gray-500 ml-auto">
                        {simulation.progress.current}/{simulation.progress.total}
                      </span>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Progress Bar */}
            {simulation.progress && (
              <div className="mb-4">
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-500 h-2 rounded-full transition-all duration-200"
                    style={{
                      width: `${(simulation.progress.current / simulation.progress.total) * 100}%`,
                    }}
                  />
                </div>
              </div>
            )}

            {/* Live Logs */}
            {simulation.logs && simulation.logs.length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-2">Live Log</h3>
                <div
                  ref={logContainerRef}
                  className="bg-gray-900 text-green-400 p-3 rounded-lg text-xs font-mono h-32 overflow-y-auto"
                >
                  {simulation.logs.map((log, i) => (
                    <div key={i}>
                      <span className="text-gray-500">[{log.timestamp}]</span> {log.message}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {isError && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <h2 className="text-red-700 font-semibold mb-2">Simulation Failed</h2>
            <p className="text-red-600">{simulation.error}</p>
            <button
              onClick={() => router.push("/")}
              className="mt-4 text-blue-600 hover:underline"
            >
              Try Again
            </button>
          </div>
        )}

        {isComplete && result && (
          <div className="space-y-6">
            {/* Question Title */}
            {result.question && (
              <div className="text-center">
                <h2 className="text-xl font-semibold text-gray-800 mb-2">
                  {result.question}
                </h2>
              </div>
            )}

            {/* Signal Banner */}
            <div className="bg-white rounded-lg shadow-md p-4">
              <div className="text-center">
                <span
                  className={`inline-block px-6 py-3 rounded-lg font-bold text-lg ${
                    result.signal === "BUY_YES"
                      ? "bg-green-100 text-green-700"
                      : result.signal === "BUY_NO"
                      ? "bg-red-100 text-red-700"
                      : "bg-gray-100 text-gray-700"
                  }`}
                >
                  {result.signal === "BUY_YES"
                    ? "BUY YES"
                    : result.signal === "BUY_NO"
                    ? "BUY NO"
                    : "HOLD"}
                </span>
                <div className="mt-2 text-sm text-gray-600">
                  Simulation: {Math.round(result.probability * 100)}% ± {Math.round(result.ci_95[1] * 100 - result.probability * 100)}% |
                  Market: {Math.round(result.market_odds * 100)}% |
                  Diff: {result.difference > 0 ? "+" : ""}{Math.round(result.difference * 100)}pp
                  {ev && (
                    <> | EV: {ev.value > 0 ? "+" : ""}{ev.value}/100 on {ev.recommended}</>
                  )}
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-md p-6">
              {/* Main Results */}
              <div className="grid grid-cols-2 gap-6 mb-6">
                <div className="text-center p-4 bg-blue-50 rounded-lg">
                  <div className="text-3xl font-bold text-blue-600">
                    {Math.round(result.probability * 100)}%
                  </div>
                  <div className="text-sm text-gray-600 mt-1">Simulation</div>
                </div>
                <div className="text-center p-4 bg-gray-50 rounded-lg">
                  <div className="text-3xl font-bold text-gray-600">
                    {Math.round(result.market_odds * 100)}%
                  </div>
                  <div className="text-sm text-gray-600 mt-1">Market</div>
                </div>
              </div>

              {/* Details */}
              <div className="border-t pt-4 text-sm text-gray-600 space-y-2">
                <div className="flex justify-between">
                  <span>Confidence Interval (95%)</span>
                  <span>
                    {Math.round(result.ci_95[0] * 100)}% - {Math.round(result.ci_95[1] * 100)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Monte Carlo Runs</span>
                  <span>{result.n_runs}</span>
                </div>
                {ev && (
                  <div className="flex justify-between">
                    <span>Expected Value</span>
                    <span className={ev.value > 0 ? "text-green-600 font-medium" : "text-red-600"}>
                      {ev.value > 0 ? "+" : ""}{ev.value}/100 on {ev.recommended}
                    </span>
                  </div>
                )}
              </div>
            </div>

            {/* Charts Section */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="font-medium text-gray-700 mb-4">Simulation Results</h3>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Bar Chart - Final Results */}
                <div>
                  <h4 className="text-sm font-medium text-gray-600 mb-2 text-center">Final Results</h4>
                  {barChartData.length > 0 && (
                    <Plot
                      data={marketOddsLine ? [...barChartData, marketOddsLine] : barChartData}
                      layout={{
                        autosize: true,
                        height: 250,
                        margin: { l: 40, r: 20, t: 10, b: 40 },
                        xaxis: { title: { text: "Outcome" } },
                        yaxis: { title: { text: "Count" } },
                        paper_bgcolor: "transparent",
                        plot_bgcolor: "transparent",
                        showlegend: false,
                      }}
                      config={{ responsive: true, displayModeBar: false }}
                      style={{ width: "100%" }}
                    />
                  )}
                </div>

                {/* Convergence Chart */}
                <div>
                  <h4 className="text-sm font-medium text-gray-600 mb-2 text-center">Convergence Over Time</h4>
                  {convergenceData && (
                    <Plot
                      data={[
                        convergenceData.upperBound,
                        convergenceData.lowerBound,
                        convergenceData.probability,
                        convergenceData.marketLine,
                      ]}
                      layout={{
                        autosize: true,
                        height: 250,
                        margin: { l: 40, r: 20, t: 10, b: 40 },
                        xaxis: { title: { text: "Run #" } },
                        yaxis: {
                          title: { text: "Probability (%)" },
                          range: [0, 100],
                        },
                        paper_bgcolor: "transparent",
                        plot_bgcolor: "transparent",
                        showlegend: false,
                      }}
                      config={{ responsive: true, displayModeBar: false }}
                      style={{ width: "100%" }}
                    />
                  )}
                </div>
              </div>
            </div>

            {/* Model Explainer */}
            {result.model_explanation && (
              <ModelExplainer explanation={result.model_explanation as ModelExplanation} />
            )}

            {/* Actions */}
            <div className="flex gap-3">
              <button
                onClick={() => router.push("/")}
                className="flex-1 py-2 px-4 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                New Simulation
              </button>
              {result.model_code && (
                <button
                  onClick={downloadModel}
                  className="flex-1 py-2 px-4 border border-green-500 text-green-600 rounded-lg hover:bg-green-50 transition-colors"
                >
                  Download Model
                </button>
              )}
              <button
                onClick={downloadResult}
                className="flex-1 py-2 px-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Download JSON
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
