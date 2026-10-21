import { API_URL, AuthError, type Menu } from "./api";

export type AdminCafe = { id: number; slug: string; name_ar: string; name_en: string };

export type AdminCategory = { id: number; name_ar: string; name_en: string; position: number };

export type AdminProduct = {
  id: number;
  category_id: number;
  name_ar: string;
  name_en: string;
  description_ar: string | null;
  description_en: string | null;
  price: number; // halalas
  price_sar: string; // "18.50"
  available: boolean;
  image_url: string | null;
  position: number;
};

/** A Café's whole Menu for editing, unavailable Products included. */
export type AdminMenu = { cafe: Menu["cafe"]; categories: AdminCategory[]; products: AdminProduct[] };

export type CategoryInput = { name_ar: string; name_en: string };

export type ProductInput = {
  category_id: number;
  name_ar: string;
  name_en: string;
  description_ar: string;
  description_en: string;
  price_sar: string; // SAR as typed, e.g. "18.50"; the API stores halalas
  available: boolean;
  image_url: string;
};

/** 409: a Category that still has Products, a Product that is on past Orders, or a taken slug or username. */
export class ConflictError extends Error {
  /** The API's `detail`; "slug_taken" or "username_taken" when adding a Café. */
  constructor(readonly detail: string = "") {
    super(detail);
  }
}

/** 422: the API refused the input (missing Arabic name, bad price, …). */
export class InvalidInputError extends Error {}

async function request<T>(token: string, method: string, path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${API_URL}/api/admin${path}`, {
    method,
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
    cache: "no-store",
  });
  if (res.status === 401 || res.status === 403) throw new AuthError();
  if (res.status === 409) throw new ConflictError((await res.json().catch(() => ({}))).detail);
  if (res.status === 422) throw new InvalidInputError();
  if (!res.ok) throw new Error(`Admin request failed: ${res.status}`);
  return res.status === 204 ? (undefined as T) : res.json();
}

export const listCafes = (token: string) => request<AdminCafe[]>(token, "GET", "/cafes");

export type CafeInput = {
  name_ar: string;
  name_en: string;
  slug: string;
  barista_username: string;
  barista_password: string;
};

/** Adds a Café (empty Menu) and its Barista login. */
export const createCafe = (token: string, input: CafeInput) => request<AdminCafe>(token, "POST", "/cafes", input);

export const getAdminMenu = (token: string, cafeId: number) =>
  request<AdminMenu>(token, "GET", `/cafes/${cafeId}/menu`);

export const createCategory = (token: string, cafeId: number, input: CategoryInput) =>
  request<AdminCategory>(token, "POST", `/cafes/${cafeId}/categories`, input);

export const updateCategory = (token: string, cafeId: number, id: number, input: Partial<CategoryInput>) =>
  request<AdminCategory>(token, "PATCH", `/cafes/${cafeId}/categories/${id}`, input);

export const deleteCategory = (token: string, cafeId: number, id: number) =>
  request<void>(token, "DELETE", `/cafes/${cafeId}/categories/${id}`);

export const createProduct = (token: string, cafeId: number, input: ProductInput) =>
  request<AdminProduct>(token, "POST", `/cafes/${cafeId}/products`, input);

export const updateProduct = (token: string, cafeId: number, id: number, input: Partial<ProductInput>) =>
  request<AdminProduct>(token, "PATCH", `/cafes/${cafeId}/products/${id}`, input);

export const deleteProduct = (token: string, cafeId: number, id: number) =>
  request<void>(token, "DELETE", `/cafes/${cafeId}/products/${id}`);
