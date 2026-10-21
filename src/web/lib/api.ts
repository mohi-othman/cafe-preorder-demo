export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type Product = {
  id: number;
  name_ar: string;
  name_en: string;
  description_ar: string | null;
  description_en: string | null;
  price: number; // halalas
  image_url: string | null;
};

export type Category = {
  id: number;
  name_ar: string;
  name_en: string;
  products: Product[];
};

export type Menu = {
  cafe: { slug: string; name_ar: string; name_en: string };
  categories: Category[];
};

/** The Café's Menu, or null if the Café doesn't exist. */
export async function getMenu(slug: string): Promise<Menu | null> {
  const res = await fetch(`${API_URL}/api/cafes/${encodeURIComponent(slug)}/menu`, { cache: "no-store" });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`Menu request failed: ${res.status}`);
  return res.json();
}

export type PickupType = "table" | "car";

export type OrderStatus = "awaiting_payment" | "pending" | "preparing" | "ready" | "completed";

export type OrderLine = {
  product_id: number;
  name_ar: string;
  name_en: string;
  unit_price: number; // halalas
  qty: number;
  note: string | null;
};

export type Order = {
  id: string; // uuid, used in /o/<uuid>
  cafe: Menu["cafe"];
  status: OrderStatus;
  order_number: number | null;
  customer_name: string;
  phone: string | null;
  pickup_type: PickupType;
  table_number: string | null;
  car_model: string | null;
  car_color: string | null;
  car_plate: string | null;
  total: number; // halalas
  created_at: string;
  paid_at: string | null;
  lines: OrderLine[];
};

export type NewOrder = {
  customer_name: string;
  phone: string | null;
  pickup_type: PickupType;
  table_number: string | null;
  car_model: string | null;
  car_color: string | null;
  car_plate: string | null;
  lines: { product_id: number; qty: number; note: string | null }[];
};

export type PaymentMethod = "apple_pay" | "mada";

/** Create an Order (awaiting payment). Throws on validation errors. */
export async function createOrder(slug: string, order: NewOrder): Promise<Order> {
  const res = await fetch(`${API_URL}/api/cafes/${encodeURIComponent(slug)}/orders`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(order),
  });
  if (!res.ok) throw new Error(`Create order failed: ${res.status}`);
  return res.json();
}

/** Pay through the fake provider; `source: "fail"` simulates a decline. Returns null when declined. */
export async function payOrder(id: string, method: PaymentMethod, source: "ok" | "fail" = "ok"): Promise<Order | null> {
  const res = await fetch(`${API_URL}/api/orders/${encodeURIComponent(id)}/pay`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ method, source }),
  });
  if (res.status === 402) return null;
  if (!res.ok) throw new Error(`Payment request failed: ${res.status}`);
  return res.json();
}

/** The Order, or null if there is no such Order. */
export async function getOrder(id: string): Promise<Order | null> {
  const res = await fetch(`${API_URL}/api/orders/${encodeURIComponent(id)}`, { cache: "no-store" });
  if (res.status === 404 || res.status === 422) return null;
  if (!res.ok) throw new Error(`Order request failed: ${res.status}`);
  return res.json();
}
