"use client";

import { useLang } from "@/lib/useLang";
import styles from "../admin.module.css";

/** Placeholder; ticket 08 builds the QR page. */
export default function QrPage() {
  const { t } = useLang();
  return (
    <>
      <div className={styles.head}>
        <h2 className="serif">{t("admin.nav.qr")}</h2>
      </div>
      <p className={styles.empty}>{t("admin.comingSoon")}</p>
    </>
  );
}
