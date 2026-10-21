"use client";

import { useLang } from "@/lib/useLang";
import { useAdmin } from "../AdminShell";
import styles from "../admin.module.css";

/** Cafés list. Ticket 08 adds the "add café" form. */
export default function CafesPage() {
  const { t } = useLang();
  const { cafes } = useAdmin();
  return (
    <>
      <div className={styles.head}>
        <h2 className="serif">{t("admin.cafes.title")}</h2>
      </div>
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
