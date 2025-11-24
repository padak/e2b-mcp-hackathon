export interface MarketData {
  question: string;
  slug: string;
  yes_odds: number;
  volume: number;
  end_date: string;
  active: boolean;
  outcomes: number;
}

export interface MarketValidation {
  valid: boolean;
  simulatable: boolean;
  market: MarketData | null;
  reason: string | null;
}

export interface SimulationStatus {
  id: string;
  status: 'pending' | 'research' | 'generate' | 'calibrate' | 'simulate' | 'complete' | 'error';
  progress?: {
    current: number;
    total: number;
  };
  result?: SimulationResult;
  error?: string;
}

export interface SimulationResult {
  question?: string;
  probability: number;
  ci_95: [number, number];
  n_runs: number;
  market_odds: number;
  difference: number;
  signal: 'BUY_YES' | 'BUY_NO' | 'HOLD';
  expected_value?: number;
  outcomes?: number[];
  model_explanation?: ModelExplanation;
  model_code?: string;
}

export interface LogEntry {
  timestamp: string;
  message: string;
}

export interface AgentDefinition {
  count: number;
  why: string;
  behavior: string;
  initial_state: string;
}

export interface ModelExplanation {
  research_highlights: string[];
  agents: Record<string, AgentDefinition>;
  simulation_logic: string[];
  outcome_interpretation: string;
}
