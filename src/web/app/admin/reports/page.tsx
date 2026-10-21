"use client";

import { useLang } from "@/lib/useLang";
import styles from "../admin.module.css";

/** Placeholder; ticket 09 builds the Reports page. */
export default function ReportsPage() {
  const { t } = useLang();
  return (
    <>
      <div className={styles.head}>
        <h2 className="serif">{t("admin.nav.reports")}</h2>
      </div>
      <p className={styles.empty}>{t("admin.comingSoon")}</p>
    </>
  );
}
