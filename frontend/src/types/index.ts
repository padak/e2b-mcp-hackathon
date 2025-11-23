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
  probability: number;
  ci_95: [number, number];
  n_runs: number;
  market_odds: number;
  difference: number;
  signal: 'BUY_YES' | 'BUY_NO' | 'HOLD';
  expected_value?: number;
  outcomes?: number[];
}

export interface LogEntry {
  timestamp: string;
  message: string;
}
