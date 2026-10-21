"use client";

import QRCode from "qrcode";
import { useEffect, useState } from "react";
import { useLang } from "@/lib/useLang";
import { useAdmin } from "../AdminShell";
import styles from "../admin.module.css";

/** The customer link a QR code opens: /c/<slug>?table=N, or /c/<slug> for car pickup. */
function menuUrl(origin: string, slug: string, table: string): string {
  const base = `${origin}/c/${encodeURIComponent(slug)}`;
  return table ? `${base}?table=${encodeURIComponent(table)}` : base;
}

/** QR page for the Café picked in the sidebar: optional table number, printable QR card. */
export default function QrPage() {
  const { t, localized } = useLang();
  const { cafe } = useAdmin();
  const [table, setTable] = useState("");
  const [qr, setQr] = useState<{ url: string; image: string } | null>(null);

  // The admin shell renders only in the browser, so window is available here.
  const url = cafe ? menuUrl(window.location.origin, cafe.slug, table.trim()) : null;

  useEffect(() => {
    if (!url) return;
    let current = true;
    QRCode.toDataURL(url, { errorCorrectionLevel: "M", margin: 2, width: 320 }).then((image) => {
      if (current) setQr({ url, image });
    });
    return () => {
      current = false;
    };
  }, [url]);

  if (!cafe) {
    return (
      <>
        <div className={styles.head}>
          <h2 className="serif">{t("admin.nav.qr")}</h2>
        </div>
        <p className={styles.empty}>{t("admin.noCafes")}</p>
      </>
    );
  }

  return (
    <>
      <div className={styles.head}>
        <h2 className="serif">{t("admin.nav.qr")}</h2>
        <button className={styles.btn} onClick={() => window.print()} disabled={qr?.url !== url}>
          {t("admin.qr.print")}
        </button>
      </div>
      <div className={styles.form}>
        <label>
          {t("admin.qr.table")}
          <input
            inputMode="numeric"
            dir="ltr"
            value={table}
            onChange={(e) => setTable(e.target.value)}
            className={styles.tableInput}
          />
          <small>{t("admin.qr.tableHint")}</small>
        </label>
      </div>
      {qr?.url === url && (
        <section className={styles.qrCard} aria-label={t("admin.nav.qr")}>
          <div className={`serif ${styles.qrCafe}`}>{localized(cafe.name_ar, cafe.name_en)}</div>
          <div className={styles.qrFor}>
            {table.trim() ? t("admin.qr.forTable", { n: table.trim() }) : t("admin.qr.forCar")}
          </div>
          {/* eslint-disable-next-line @next/next/no-img-element -- a generated data: URL */}
          <img src={qr.image} width={320} height={320} alt={qr.url} className={styles.qrImage} />
          <div className={styles.qrScan}>{t("admin.qr.scan")}</div>
          <a className={styles.qrUrl} dir="ltr" href={qr.url} target="_blank" rel="noreferrer" data-testid="qr-url">
            {qr.url}
          </a>
        </section>
      )}
    </>
  );
}
