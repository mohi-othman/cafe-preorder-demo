"use client";

import { useState } from "react";
import Image from "next/image";
import LangToggle from "@/components/LangToggle";
import type { Menu } from "@/lib/api";
import { useLang } from "@/lib/useLang";
import styles from "./menu.module.css";

const PLACEHOLDER = "/menu/placeholder.svg";

export default function MenuView({ menu, table }: { menu: Menu; table: string | null }) {
  const { t, localized, formatPrice } = useLang();
  const [query, setQuery] = useState("");
  const [categoryId, setCategoryId] = useState<number | null>(null);

  const cafeName = localized(menu.cafe.name_ar, menu.cafe.name_en);
  const q = query.trim().toLowerCase();
  const sections = menu.categories
    .filter((c) => categoryId === null || c.id === categoryId)
    .map((c) => ({
      ...c,
      products: c.products.filter(
        (p) => !q || p.name_ar.toLowerCase().includes(q) || p.name_en.toLowerCase().includes(q),
      ),
    }))
    .filter((c) => c.products.length > 0);
  const chips = menu.categories.filter((c) => c.products.length > 0);

  return (
    <main className={styles.page}>
      <header className={styles.top}>
        <div className={`${styles.logo} serif`} aria-hidden>
          {cafeName.charAt(0)}
        </div>
        <div>
          <h1 className="serif">{cafeName}</h1>
          {table && <small>{t("menu.table", { table })}</small>}
        </div>
        <LangToggle className={styles.lang} />
      </header>

      <input
        className={styles.search}
        type="search"
        placeholder={t("menu.search")}
        aria-label={t("menu.search")}
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />

      <nav className={styles.chips}>
        <button
          className={`${styles.chip} ${categoryId === null ? styles.on : ""}`}
          onClick={() => setCategoryId(null)}
        >
          {t("menu.all")}
        </button>
        {chips.map((c) => (
          <button
            key={c.id}
            className={`${styles.chip} ${categoryId === c.id ? styles.on : ""}`}
            onClick={() => setCategoryId(c.id)}
          >
            {localized(c.name_ar, c.name_en)}
          </button>
        ))}
      </nav>

      {sections.length === 0 && <p className={styles.status}>{t("menu.empty")}</p>}

      {sections.map((c) => (
        <section key={c.id}>
          <h2 className={`${styles.sec} serif`}>{localized(c.name_ar, c.name_en)}</h2>
          {c.products.map((p) => {
            const name = localized(p.name_ar, p.name_en);
            const description = localized(p.description_ar ?? "", p.description_en);
            return (
              <article key={p.id} className={styles.item}>
                <Image
                  className={styles.img}
                  src={p.image_url || PLACEHOLDER}
                  alt=""
                  width={72}
                  height={72}
                  unoptimized
                />
                <div className={styles.text}>
                  <b>{name}</b>
                  {description && <p>{description}</p>}
                  <span className={styles.price}>{formatPrice(p.price)}</span>
                </div>
                <button className={styles.add} aria-label={t("menu.add", { name })}>
                  +
                </button>
              </article>
            );
          })}
        </section>
      ))}
    </main>
  );
}
