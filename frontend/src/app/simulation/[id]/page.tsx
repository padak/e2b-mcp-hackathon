"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { SimulationStatus } from "@/types";

const PHASE_LABELS: Record<string, string> = {
  pending: "Starting...",
  research: "Researching market context",
  generate: "Generating simulation model",
  calibrate: "Calibrating threshold",
  simulate: "Running Monte Carlo",
  complete: "Complete",
  error: "Error",
};

export default function SimulationPage() {
  const params = useParams();
  const router = useRouter();
  const [simulation, setSimulation] = useState<SimulationStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

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
        const data: SimulationStatus = await res.json();
        setSimulation(data);

        // Continue polling if not complete
        if (data.status !== "complete" && data.status !== "error") {
          setTimeout(pollStatus, 500);
        }
      } catch {
        setError("Failed to fetch simulation status");
      }
    };

    pollStatus();
  }, [id]);

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

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-8">
      <div className="w-full max-w-xl">
        <h1 className="text-3xl font-bold text-center mb-8">
          {isComplete ? "Results" : "Simulating..."}
        </h1>

        {!isComplete && !isError && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            {/* Progress Steps */}
            <div className="space-y-4">
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
              <div className="mt-4">
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

        {isComplete && simulation.result && (
          <div className="bg-white rounded-lg shadow-md p-6">
            {/* Main Results */}
            <div className="grid grid-cols-2 gap-6 mb-6">
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <div className="text-3xl font-bold text-blue-600">
                  {Math.round(simulation.result.probability * 100)}%
                </div>
                <div className="text-sm text-gray-600 mt-1">Simulation</div>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="text-3xl font-bold text-gray-600">
                  {Math.round(simulation.result.market_odds * 100)}%
                </div>
                <div className="text-sm text-gray-600 mt-1">Market</div>
              </div>
            </div>

            {/* Signal */}
            <div className="text-center mb-6">
              <span
                className={`inline-block px-4 py-2 rounded-full font-semibold ${
                  simulation.result.signal === "BUY_YES"
                    ? "bg-green-100 text-green-700"
                    : simulation.result.signal === "BUY_NO"
                    ? "bg-red-100 text-red-700"
                    : "bg-gray-100 text-gray-700"
                }`}
              >
                {simulation.result.signal === "BUY_YES"
                  ? `BUY YES (+${Math.round(simulation.result.difference * 100)}pp)`
                  : simulation.result.signal === "BUY_NO"
                  ? `BUY NO (${Math.round(simulation.result.difference * 100)}pp)`
                  : "HOLD"}
              </span>
            </div>

            {/* Details */}
            <div className="border-t pt-4 text-sm text-gray-600 space-y-2">
              <div className="flex justify-between">
                <span>Confidence Interval (95%)</span>
                <span>
                  {Math.round(simulation.result.ci_95[0] * 100)}% -{" "}
                  {Math.round(simulation.result.ci_95[1] * 100)}%
                </span>
              </div>
              <div className="flex justify-between">
                <span>Monte Carlo Runs</span>
                <span>{simulation.result.n_runs}</span>
              </div>
            </div>

            {/* Actions */}
            <div className="mt-6 flex gap-4">
              <button
                onClick={() => router.push("/")}
                className="flex-1 py-2 px-4 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                New Simulation
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
