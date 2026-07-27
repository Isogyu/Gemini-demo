export type AccountCategory =
  | "asset"
  | "liability"
  | "equity"
  | "revenue"
  | "expense";

export interface TrialBalanceLine {
  account_code: string;
  account_name: string;
  category: AccountCategory;
  debit: number;
  credit: number;
}

export interface TrialBalance {
  name: string;
  fiscal_year: number;
  lines: TrialBalanceLine[];
}

export interface EntertainmentInput {
  total_expense: number;
  food_and_drink_expense: number;
}

export interface DepreciationAssetInput {
  asset_name: string;
  booked_depreciation: number;
  tax_limit: number;
}

export interface SampleDataset {
  id: string;
  label: string;
  company_name: string;
  fiscal_year: number;
  capital: number;
  trial_balance: TrialBalance;
  entertainment: EntertainmentInput;
  depreciation_assets: DepreciationAssetInput[];
  other_additions: number;
  other_subtractions: number;
}

export interface ReconciliationEntry {
  label: string;
  kind: "addition" | "subtraction";
  amount: number;
  note: string;
}

export interface TaxBreakdown {
  corporate_tax: number;
  local_corporate_tax: number;
  enterprise_tax: number;
  inhabitant_tax: number;
  total_tax: number;
  effective_tax_rate: number;
}

export interface ReconciliationResult {
  company_name: string;
  fiscal_year: number;
  capital: number;
  net_income_before_tax: number;
  total_additions: number;
  total_subtractions: number;
  taxable_income: number;
  tax: TaxBreakdown;
  after_tax_profit: number;
  entries: ReconciliationEntry[];
}

export interface ReconciliationRequest {
  company_name: string;
  fiscal_year: number;
  capital: number;
  trial_balance: TrialBalance;
  entertainment: EntertainmentInput;
  depreciation_assets: DepreciationAssetInput[];
  other_additions: number;
  other_subtractions: number;
  effective_tax_rate: number;
}
