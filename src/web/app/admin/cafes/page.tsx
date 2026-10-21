"use client";

import { useState, type FormEvent } from "react";
import { ConflictError, createCafe, InvalidInputError } from "@/lib/adminApi";
import type { Key } from "@/lib/i18n";
import { useLang } from "@/lib/useLang";
import { useAdmin } from "../AdminShell";
import styles from "../admin.module.css";

const EMPTY = { name_ar: "", name_en: "", slug: "", barista_username: "", barista_password: "" };

/** Cafés list plus the "add café" form (names, slug, Barista login). */
export default function CafesPage() {
  const { t, localized } = useLang();
  const { token, cafes, reloadCafes, handleAuthError } = useAdmin();
  const [form, setForm] = useState<typeof EMPTY | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<Key | null>(null);
  const [added, setAdded] = useState<string | null>(null);

  const field = (name: keyof typeof EMPTY) => ({
    value: form?.[name] ?? "",
    onChange: (e: { target: { value: string } }) => setForm((f) => f && { ...f, [name]: e.target.value }),
  });

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (!form) return;
    setBusy(true);
    setError(null);
    try {
      const cafe = await createCafe(token, form);
      await reloadCafes();
      setForm(null);
      setAdded(localized(cafe.name_ar, cafe.name_en));
    } catch (err) {
      if (!handleAuthError(err)) {
        setError(
          err instanceof ConflictError
            ? err.detail === "username_taken"
              ? "admin.cafes.usernameTaken"
              : "admin.cafes.slugTaken"
            : err instanceof InvalidInputError
              ? "admin.cafes.invalid"
              : "admin.error",
        );
      }
    }
    setBusy(false);
  }

  return (
    <>
      <div className={styles.head}>
        <h2 className="serif">{t("admin.cafes.title")}</h2>
        {!form && (
          <button
            className={styles.btn}
            onClick={() => {
              setForm(EMPTY);
              setAdded(null);
              setError(null);
            }}
          >
            {t("admin.cafes.add")}
          </button>
        )}
      </div>

      {added && (
        <p className={styles.notice} role="status">
          {t("admin.cafes.added", { name: added })}
        </p>
      )}

      {form && (
        <form className={styles.form} onSubmit={submit}>
          <h3>{t("admin.cafes.new")}</h3>
          {error && (
            <p className={styles.error} role="alert">
              {t(error)}
            </p>
          )}
          <div className={styles.sideBySide}>
            <label>
              {t("admin.form.nameAr")}
              <input dir="rtl" lang="ar" required autoFocus {...field("name_ar")} />
            </label>
            <label>
              {t("admin.form.nameEn")}
              <input dir="ltr" lang="en" {...field("name_en")} />
            </label>
          </div>
          <label>
            {t("admin.cafes.slug")}
            <input
              dir="ltr"
              required
              pattern="[a-z0-9]+(-[a-z0-9]+)*"
              autoCapitalize="none"
              spellCheck={false}
              {...field("slug")}
            />
            <small>{t("admin.cafes.slugHint")}</small>
          </label>
          <fieldset className={styles.group}>
            <legend>{t("admin.cafes.baristaLogin")}</legend>
            <div className={styles.sideBySide}>
              <label>
                {t("admin.username")}
                <input dir="ltr" required autoCapitalize="none" autoComplete="off" {...field("barista_username")} />
              </label>
              <label>
                {t("admin.password")}
                <input
                  dir="ltr"
                  type="password"
                  required
                  minLength={8}
                  autoComplete="new-password"
                  {...field("barista_password")}
                />
                <small>{t("admin.cafes.passwordHint")}</small>
              </label>
            </div>
          </fieldset>
          <div className={styles.formActions}>
            <button className={styles.btn} disabled={busy}>
              {t("admin.save")}
            </button>
            <button type="button" className={styles.textBtn} onClick={() => setForm(null)}>
              {t("admin.cancel")}
            </button>
          </div>
        </form>
      )}

      {cafes.length === 0 ? (
        <p className={styles.empty}>{t("admin.noCafes")}</p>
      ) : (
        <table className={styles.table}>
          <thead>
            <tr>
              <th>{t("admin.col.nameAr")}</th>
              <th>{t("admin.col.nameEn")}</th>
              <th>{t("admin.cafes.link")}</th>
            </tr>
          </thead>
          <tbody>
            {cafes.map((c) => (
              <tr key={c.id}>
                <td>{c.name_ar}</td>
                <td>
                  <bdi dir="ltr">{c.name_en}</bdi>
                </td>
                <td>
                  <a className={styles.link} dir="ltr" href={`/c/${c.slug}`} target="_blank" rel="noreferrer">
                    /c/{c.slug}
                  </a>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </>
  );
}
