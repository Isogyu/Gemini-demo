const yenFormatter = new Intl.NumberFormat("ja-JP", {
  style: "currency",
  currency: "JPY",
  maximumFractionDigits: 0,
});

export function formatYen(value: number): string {
  return yenFormatter.format(Math.round(value));
}

export function formatPercent(value: number): string {
  return `${(value * 100).toFixed(2)}%`;
}
