export function money(value: string | number): string {
  const amount = typeof value === "number" ? value : Number(value);
  return `$${amount.toFixed(2)}`;
}

export function pickupWindow(start: string, end: string): string {
  const from = new Date(start);
  const to = new Date(end);
  return `${from.toLocaleString()} – ${to.toLocaleString()}`;
}

export function depositDue(price: string, quantity: number, rate = 0.5): string {
  return money(Number(price) * quantity * rate);
}
