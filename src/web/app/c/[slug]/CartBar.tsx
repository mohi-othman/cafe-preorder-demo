"use client";

import Link from "next/link";
import { useCart } from "@/lib/cart";
import { useLang } from "@/lib/useLang";
import styles from "../../order.module.css";

/** Floating ink bar with the cart's count and total; links to checkout. */
export default function CartBar({ slug, table }: { slug: string; table: string | null }) {
  const { t, formatPrice } = useLang();
  const { count, total } = useCart(slug);
  if (count === 0) return null;
  const query = table ? `?table=${encodeURIComponent(table)}` : "";
  return (
    <Link className={styles.cartbar} href={`/c/${encodeURIComponent(slug)}/checkout${query}`}>
      <span className={styles.count} aria-label={t("cart.count", { count })}>
        {count}
      </span>
      <span className={styles.barLabel}>{t("cart.view")}</span>
      <span>{formatPrice(total)}</span>
    </Link>
  );
}
