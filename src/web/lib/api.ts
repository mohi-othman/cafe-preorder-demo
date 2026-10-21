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
