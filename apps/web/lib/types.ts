export type Contributor = {
  feature: string;
  label: string;
  factor: string;
  percentile: number;
  contribution: number;
  explanation: string;
};

export type Recommendation = {
  symbol: string;
  company_name: string;
  exchange?: string;
  sector: string | null;
  as_of_date: string;
  model_version?: string;
  score: number | null;
  band: string;
  confidence: number;
  confidence_label?: string;
  confidence_help: string;
  factor_scores: Record<string, number | null>;
  raw_features?: Record<string, number | null>;
  contributors: Contributor[];
  warnings: string[];
  freshness?: Record<string, unknown>;
  latest_price?: number | null;
  price_date?: string;
  risk_metrics?: Record<string, number | null>;
  what_could_change?: string[];
  history?: { date: string; close: number }[];
  demo?: boolean;
  data_mode?: string;
  disclosure?: string;
};

export type ApiError = { error?: { message?: string } };
