"use client";

import { useState, type FormEvent } from "react";
import type { AdminCategory, CategoryInput } from "@/lib/adminApi";
import { useLang } from "@/lib/useLang";
import styles from "../admin.module.css";

/** Add or rename a Category: Arabic and English names side by side. */
export default function CategoryForm(props: {
  category: AdminCategory | null;
  onSave: (input: CategoryInput) => Promise<void>;
  onCancel: () => void;
}) {
  const { t } = useLang();
  const [nameAr, setNameAr] = useState(props.category?.name_ar ?? "");
  const [nameEn, setNameEn] = useState(props.category?.name_en ?? "");
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    await props.onSave({ name_ar: nameAr, name_en: nameEn });
    setBusy(false);
  }

  return (
    <form className={styles.form} onSubmit={submit}>
      <h3>{t(props.category ? "admin.editCategory" : "admin.form.newCategory")}</h3>
      <div className={styles.sideBySide}>
        <label>
          {t("admin.form.nameAr")}
          <input dir="rtl" lang="ar" value={nameAr} onChange={(e) => setNameAr(e.target.value)} required autoFocus />
        </label>
        <label>
          {t("admin.form.nameEn")}
          <input dir="ltr" lang="en" value={nameEn} onChange={(e) => setNameEn(e.target.value)} />
        </label>
      </div>
      <div className={styles.formActions}>
        <button className={styles.btn} disabled={busy}>
          {t("admin.save")}
        </button>
        <button type="button" className={styles.textBtn} onClick={props.onCancel}>
          {t("admin.cancel")}
        </button>
      </div>
    </form>
  );
}
