import { useSyncExternalStore } from "react";
import type { Product } from "./api";

/** One cart line per Product. Prices here are for display; the API recomputes the total. */
export type CartLine = {
  product: Pick<Product, "id" | "name_ar" | "name_en" | "price" | "image_url">;
  qty: number;
  note: string;
};

const EMPTY: CartLine[] = [];
const listeners = new Set<() => void>();
const cache = new Map<string, { raw: string | null; lines: CartLine[] }>();

const storageKey = (slug: string) => `qahwati.cart.${slug}`;

function read(slug: string): CartLine[] {
  let raw: string | null = null;
  try {
    raw = localStorage.getItem(storageKey(slug));
  } catch {}
  const hit = cache.get(slug);
  if (hit && hit.raw === raw) return hit.lines;
  let lines = EMPTY;
  try {
    lines = raw ? JSON.parse(raw) : EMPTY;
  } catch {}
  cache.set(slug, { raw, lines });
  return lines;
}

function write(slug: string, lines: CartLine[]) {
  try {
    if (lines.length) localStorage.setItem(storageKey(slug), JSON.stringify(lines));
    else localStorage.removeItem(storageKey(slug));
  } catch {}
  listeners.forEach((l) => l());
}

function subscribe(listener: () => void) {
  listeners.add(listener);
  window.addEventListener("storage", listener);
  return () => {
    listeners.delete(listener);
    window.removeEventListener("storage", listener);
  };
}

export function clearCart(slug: string) {
  write(slug, EMPTY);
}

export function useCart(slug: string) {
  const lines = useSyncExternalStore(subscribe, () => read(slug), () => EMPTY);
  const update = (productId: number, change: (line: CartLine) => CartLine | null) =>
    write(
      slug,
      read(slug).flatMap((l) => (l.product.id === productId ? (change(l) ?? []) : [l])),
    );

  return {
    lines,
    count: lines.reduce((n, l) => n + l.qty, 0),
    total: lines.reduce((sum, l) => sum + l.product.price * l.qty, 0),
    add(product: CartLine["product"]) {
      const current = read(slug);
      if (current.some((l) => l.product.id === product.id)) {
        update(product.id, (l) => ({ ...l, qty: l.qty + 1 }));
      } else {
        const { id, name_ar, name_en, price, image_url } = product;
        write(slug, [...current, { product: { id, name_ar, name_en, price, image_url }, qty: 1, note: "" }]);
      }
    },
    setQty(productId: number, qty: number) {
      update(productId, (l) => (qty > 0 ? { ...l, qty } : null));
    },
    setNote(productId: number, note: string) {
      update(productId, (l) => ({ ...l, note }));
    },
  };
}
