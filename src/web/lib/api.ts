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

/** Every Order status, in order; the one status list in the web code. */
export const ORDER_STATUSES = ["awaiting_payment", "pending", "preparing", "ready", "completed"] as const;
export type OrderStatus = (typeof ORDER_STATUSES)[number];

/** The statuses on the KDS board. */
export const KDS_STATUSES = ["pending", "preparing", "ready"] as const satisfies readonly OrderStatus[];
export type KdsStatus = (typeof KDS_STATUSES)[number];

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

/** Thrown by createOrder when some Products in the cart are no longer available. */
export class UnavailableProductsError extends Error {
  constructor(readonly productIds: number[]) {
    super("Products unavailable");
  }
}

/** Create an Order (awaiting payment). Throws UnavailableProductsError, or Error on other failures. */
export async function createOrder(slug: string, order: NewOrder): Promise<Order> {
  const res = await fetch(`${API_URL}/api/cafes/${encodeURIComponent(slug)}/orders`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(order),
  });
  if (res.status === 422) {
    const detail = (await res.json().catch(() => null))?.detail;
    if (detail?.code === "products_unavailable") throw new UnavailableProductsError(detail.product_ids);
  }
  if (!res.ok) throw new Error(`Create order failed: ${res.status}`);
  return res.json();
}

/**
 * Pay through the fake provider; `source: "fail"` simulates a decline. Returns null when declined.
 * If the Order was already paid (e.g. a retry after a lost response), returns the paid Order.
 */
export async function payOrder(id: string, method: PaymentMethod, source: "ok" | "fail" = "ok"): Promise<Order | null> {
  const res = await fetch(`${API_URL}/api/orders/${encodeURIComponent(id)}/pay`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ method, source }),
  });
  if (res.status === 402) return null;
  if (res.status === 409) {
    const order = await getOrder(id);
    if (order && order.status !== "awaiting_payment") return order;
  }
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

/** Thrown when the staff token is missing, expired or not allowed; the KDS logs out. */
export class AuthError extends Error {}

export type Login = {
  access_token: string;
  role: "admin" | "barista";
  cafe: Menu["cafe"] | null;
};

/** Staff login. Returns null on a wrong username or password. */
export async function login(username: string, password: string): Promise<Login | null> {
  const res = await fetch(`${API_URL}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (res.status === 401) return null;
  if (!res.ok) throw new Error(`Login failed: ${res.status}`);
  return res.json();
}

export type KdsOrder = Order & { status: KdsStatus };

export type Board = {
  cafe: Menu["cafe"];
  orders: KdsOrder[]; // oldest paid first
};

/** Headers for a staff request: the bearer token and a JSON body. */
export function authHeaders(token: string) {
  return { Authorization: `Bearer ${token}`, "Content-Type": "application/json" };
}

/** The Barista's Café and its pending, preparing and ready Orders. */
export async function getBoard(token: string): Promise<Board> {
  const res = await fetch(`${API_URL}/api/kds/orders`, { headers: authHeaders(token), cache: "no-store" });
  if (res.status === 401 || res.status === 403) throw new AuthError();
  if (!res.ok) throw new Error(`Board request failed: ${res.status}`);
  return res.json();
}

/** Move an Order one step on from `fromStatus`. Returns false when it had already moved (stale board). */
export async function advanceOrder(token: string, id: string, fromStatus: KdsStatus): Promise<boolean> {
  const res = await fetch(`${API_URL}/api/kds/orders/${encodeURIComponent(id)}/advance`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({ from_status: fromStatus }),
  });
  if (res.status === 401 || res.status === 403) throw new AuthError();
  if (res.status === 409 || res.status === 404) return false;
  if (!res.ok) throw new Error(`Advance failed: ${res.status}`);
  return true;
}
