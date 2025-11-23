"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { MarketValidation } from "@/types";

export default function Home() {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [validation, setValidation] = useState<MarketValidation | null>(null);
  const router = useRouter();

  const handleValidate = async () => {
    if (!url) return;

    setLoading(true);
    setError(null);
    setValidation(null);

    try {
      const res = await fetch(`/api/markets/from-url?url=${encodeURIComponent(url)}`);
      const data: MarketValidation = await res.json();

      if (!data.valid) {
        setError(data.reason || "Invalid market URL");
        return;
      }

      if (!data.simulatable) {
        setError(data.reason || "Market cannot be simulated");
        return;
      }

      setValidation(data);
    } catch {
      setError("Failed to validate market URL");
    } finally {
      setLoading(false);
    }
  };

  const handleSimulate = async () => {
    if (!validation?.market) return;

    setLoading(true);
    setError(null);

    try {
      const res = await fetch("/api/simulations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ market_url: url, n_runs: 200 }),
      });

      const data = await res.json();

      if (data.error) {
        setError(data.error);
        return;
      }

      router.push(`/simulation/${data.simulation_id}`);
    } catch {
      setError("Failed to start simulation");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-8">
      <main className="w-full max-w-xl">
        <h1 className="text-4xl font-bold text-center mb-2">WorldSim Markets</h1>
        <p className="text-gray-600 text-center mb-8">
          Compare Polymarket odds with AI Monte Carlo simulations
        </p>

        <div className="bg-white rounded-lg shadow-md p-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Paste Polymarket URL
          </label>
          <input
            type="url"
            value={url}
            onChange={(e) => {
              setUrl(e.target.value);
              setValidation(null);
              setError(null);
            }}
            placeholder="https://polymarket.com/event/..."
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
            onKeyDown={(e) => e.key === "Enter" && handleValidate()}
          />

          {error && (
            <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {error}
            </div>
          )}

          {!validation ? (
            <button
              onClick={handleValidate}
              disabled={loading || !url}
              className="mt-4 w-full bg-blue-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? "Validating..." : "Validate Market"}
            </button>
          ) : (
            <div className="mt-4">
              <div className="p-4 bg-green-50 border border-green-200 rounded-lg mb-4">
                <div className="flex items-center gap-2 text-green-700 font-medium mb-2">
                  <span>✓</span> Valid market detected
                </div>
                <h3 className="font-semibold text-gray-900 mb-2">
                  {validation.market?.question}
                </h3>
                <div className="grid grid-cols-3 gap-4 text-sm text-gray-600">
                  <div>
                    <span className="block font-medium">Odds</span>
                    {Math.round((validation.market?.yes_odds || 0) * 100)}% Yes
                  </div>
                  <div>
                    <span className="block font-medium">Volume</span>
                    ${validation.market?.volume?.toLocaleString()}
                  </div>
                  <div>
                    <span className="block font-medium">Ends</span>
                    {validation.market?.end_date
                      ? new Date(validation.market.end_date).toLocaleDateString()
                      : "N/A"}
                  </div>
                </div>
              </div>

              <button
                onClick={handleSimulate}
                disabled={loading}
                className="w-full bg-green-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
              >
                {loading ? "Starting..." : "Run Simulation (200 runs)"}
              </button>
            </div>
          )}
        </div>

        <p className="text-center text-gray-500 text-sm mt-6">
          Simulation takes ~2-3 minutes
        </p>
      </main>
    </div>
  );
}
