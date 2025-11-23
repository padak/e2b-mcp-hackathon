"use client";

import { useState } from "react";
import { ModelExplanation } from "@/types";

interface ModelExplainerProps {
  explanation: ModelExplanation;
}

export default function ModelExplainer({ explanation }: ModelExplainerProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full p-6 text-left font-medium text-gray-700 flex justify-between items-center hover:bg-gray-50 transition-colors"
      >
        <span className="text-lg">How We Simulated This</span>
        <span className="text-xl">{isExpanded ? "−" : "+"}</span>
      </button>

      {isExpanded && (
        <div className="px-6 pb-6 space-y-6">
          {/* Research Highlights */}
          <div>
            <h3 className="font-semibold text-gray-800 mb-3">Research Insights</h3>
            <ul className="space-y-2">
              {explanation.research_highlights.map((highlight, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-gray-600">
                  <span className="text-blue-500 mt-1">•</span>
                  {highlight}
                </li>
              ))}
            </ul>
          </div>

          {/* Agents */}
          <div>
            <h3 className="font-semibold text-gray-800 mb-3">Agent-Based Model</h3>
            <div className="space-y-4">
              {Object.entries(explanation.agents).map(([name, agent]) => (
                <div key={name} className="bg-gray-50 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-lg">
                      {name.includes("Institutional") ? "🏛️" : name.includes("Retail") ? "👥" : "📊"}
                    </span>
                    <span className="font-medium text-gray-800">{name}</span>
                    <span className="text-sm text-gray-500">({agent.count})</span>
                  </div>
                  <div className="space-y-1 text-sm">
                    <p>
                      <span className="font-medium text-gray-600">Why:</span>{" "}
                      <span className="text-gray-500">{agent.why}</span>
                    </p>
                    <p>
                      <span className="font-medium text-gray-600">Behavior:</span>{" "}
                      <span className="text-gray-500">{agent.behavior}</span>
                    </p>
                    <p>
                      <span className="font-medium text-gray-600">Initial state:</span>{" "}
                      <span className="text-gray-500">{agent.initial_state}</span>
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Simulation Logic */}
          <div>
            <h3 className="font-semibold text-gray-800 mb-3">Simulation Logic</h3>
            <ol className="space-y-2">
              {explanation.simulation_logic.map((step, i) => (
                <li key={i} className="flex items-start gap-3 text-sm text-gray-600">
                  <span className="flex-shrink-0 w-5 h-5 rounded-full bg-blue-100 text-blue-600 text-xs flex items-center justify-center font-medium">
                    {i + 1}
                  </span>
                  {step}
                </li>
              ))}
            </ol>
          </div>

          {/* Outcome Interpretation */}
          <div className="bg-blue-50 rounded-lg p-4">
            <h3 className="font-semibold text-gray-800 mb-2">Interpretation</h3>
            <p className="text-sm text-gray-600">{explanation.outcome_interpretation}</p>
          </div>
        </div>
      )}
    </div>
  );
}
