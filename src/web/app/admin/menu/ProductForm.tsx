"use client";

import { useState, type FormEvent } from "react";
import type { AdminCategory, AdminProduct, ProductInput } from "@/lib/adminApi";
import { useLang } from "@/lib/useLang";
import styles from "../admin.module.css";

/** Add or edit a Product. Arabic and English fields side by side; the price is typed in SAR. */
export default function ProductForm(props: {
  product: AdminProduct | null;
  categories: AdminCategory[];
  defaultCategoryId: number | undefined;
  onSave: (input: ProductInput) => Promise<void>;
  onDelete?: () => Promise<void>;
  onCancel: () => void;
}) {
  const { t, localized } = useLang();
  const p = props.product;
  const [form, setForm] = useState<ProductInput>({
    category_id: p?.category_id ?? props.defaultCategoryId ?? 0,
    name_ar: p?.name_ar ?? "",
    name_en: p?.name_en ?? "",
    description_ar: p?.description_ar ?? "",
    description_en: p?.description_en ?? "",
    price_sar: p?.price_sar ?? "",
    available: p?.available ?? true,
    image_url: p?.image_url ?? "",
  });
  const [busy, setBusy] = useState(false);
  const set = <K extends keyof ProductInput>(key: K, value: ProductInput[K]) => setForm((f) => ({ ...f, [key]: value }));

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    await props.onSave(form);
    setBusy(false);
  }

  return (
    <form className={styles.form} onSubmit={submit}>
      <h3>{t(p ? "admin.form.editProduct" : "admin.form.newProduct")}</h3>
      <div className={styles.sideBySide}>
        <fieldset lang="ar" dir="rtl">
          <legend>{t("admin.form.arabic")}</legend>
          <label>
            {t("admin.form.name")}
            <input value={form.name_ar} onChange={(e) => set("name_ar", e.target.value)} required autoFocus />
          </label>
          <label>
            {t("admin.form.description")}
            <textarea rows={2} value={form.description_ar} onChange={(e) => set("description_ar", e.target.value)} />
          </label>
        </fieldset>
        <fieldset lang="en" dir="ltr">
          <legend>{t("admin.form.english")}</legend>
          <label>
            {t("admin.form.name")}
            <input value={form.name_en} onChange={(e) => set("name_en", e.target.value)} />
          </label>
          <label>
            {t("admin.form.description")}
            <textarea rows={2} value={form.description_en} onChange={(e) => set("description_en", e.target.value)} />
          </label>
        </fieldset>
      </div>
      <div className={styles.row}>
        <label>
          {t("admin.form.price")}
          <input
            dir="ltr"
            inputMode="decimal"
            placeholder="18.50"
            value={form.price_sar}
            onChange={(e) => set("price_sar", e.target.value)}
            required
          />
        </label>
        <label>
          {t("admin.form.category")}
          <select value={form.category_id} onChange={(e) => set("category_id", Number(e.target.value))}>
            {props.categories.map((c) => (
              <option key={c.id} value={c.id}>
                {localized(c.name_ar, c.name_en)}
              </option>
            ))}
          </select>
        </label>
        <label className={styles.grow}>
          {t("admin.form.imageUrl")}
          <input
            dir="ltr"
            placeholder="/menu/cortado.svg"
            value={form.image_url}
            onChange={(e) => set("image_url", e.target.value)}
          />
        </label>
        <label className={styles.check}>
          <input type="checkbox" checked={form.available} onChange={(e) => set("available", e.target.checked)} />
          {t("admin.form.available")}
        </label>
      </div>
      <div className={styles.formActions}>
        <button className={styles.btn} disabled={busy}>
          {t("admin.save")}
        </button>
        <button type="button" className={styles.textBtn} onClick={props.onCancel}>
          {t("admin.cancel")}
        </button>
        {props.onDelete && (
          <button type="button" className={`${styles.textBtn} ${styles.danger} ${styles.end}`} onClick={props.onDelete}>
            {t("admin.delete")}
          </button>
        )}
      </div>
    </form>
  );
}
