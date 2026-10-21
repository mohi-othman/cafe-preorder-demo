"use client";

import { useEffect, useState } from "react";
import { getDailyReport, type DailyReport } from "@/lib/adminApi";
import { useLang } from "@/lib/useLang";
import { useAdmin } from "../AdminShell";
import styles from "../admin.module.css";
import r from "./reports.module.css";

/** Today in the Café's time zone, as YYYY-MM-DD. */
function riyadhToday(): string {
  return new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Riyadh" }).format(new Date());
}

/** Daily report of the picked Café: stat cards, top 5 Products and Orders per hour. */
export default function ReportsPage() {
  const { t, localized, formatPrice } = useLang();
  const { token, cafe, handleAuthError } = useAdmin();
  const [date, setDate] = useState(riyadhToday);
  const [report, setReport] = useState<DailyReport | null>(null);
  const [error, setError] = useState(false);
  const cafeId = cafe?.id ?? null;

  useEffect(() => {
    if (cafeId === null || !date) return;
    let stale = false;
    const id = setTimeout(async () => {
      setReport(null);
      setError(false);
      try {
        const next = await getDailyReport(token, cafeId, date);
        if (!stale) setReport(next);
      } catch (e) {
        if (!stale && !handleAuthError(e)) setError(true);
      }
    }, 0);
    return () => {
      stale = true;
      clearTimeout(id);
    };
  }, [token, cafeId, date, handleAuthError]);

  if (!cafe) return <p className={styles.empty}>{t("admin.noCafes")}</p>;

  const peak = report ? Math.max(1, ...report.orders_per_hour) : 1;

  return (
    <>
      <div className={styles.head}>
        <h2 className="serif">{t("admin.reports.title", { cafe: localized(cafe.name_ar, cafe.name_en) })}</h2>
        <label className={r.date}>
          {t("admin.reports.date")}
          <input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
        </label>
      </div>
      <p className={r.note}>{t("admin.reports.paidOnly")}</p>

      {error && (
        <p className={styles.error} role="alert">
          {t("admin.error")}
        </p>
      )}
      {!report && !error && <p className={styles.empty}>{t("common.loading")}</p>}

      {report && (
        <>
          <div className={r.stats}>
            <div className={r.stat}>
              <span>{t("admin.reports.orders")}</span>
              <strong className="serif">{report.orders}</strong>
            </div>
            <div className={r.stat}>
              <span>{t("admin.reports.revenue")}</span>
              <strong className="serif">{formatPrice(report.revenue)}</strong>
            </div>
            <div className={r.stat}>
              <span>{t("admin.reports.average")}</span>
              <strong className="serif">
                {report.average_order_value === null ? "—" : formatPrice(report.average_order_value)}
              </strong>
            </div>
          </div>

          <div className={r.panels}>
            <section className={r.panel}>
              <h3>{t("admin.reports.top")}</h3>
              {report.top_products.length === 0 ? (
                <p className={styles.empty}>{t("admin.reports.noOrders")}</p>
              ) : (
                <ol className={r.top}>
                  {report.top_products.map((p) => (
                    <li key={p.product_id}>
                      <span className={r.topName}>{localized(p.name_ar, p.name_en)}</span>
                      <span className={r.qty}>{t("admin.reports.qty", { qty: p.qty })}</span>
                      <span className={r.money}>{formatPrice(p.revenue)}</span>
                    </li>
                  ))}
                </ol>
              )}
            </section>

            <section className={r.panel}>
              <h3>{t("admin.reports.perHour")}</h3>
              <div className={r.chart}>
                {report.orders_per_hour.map((count, hour) => (
                  <div
                    key={hour}
                    className={r.col}
                    title={t("admin.reports.hourBar", { hour, count })}
                    aria-label={t("admin.reports.hourBar", { hour, count })}
                  >
                    <span className={r.count}>{count > 0 ? count : ""}</span>
                    <div className={r.track}>
                      <div className={r.bar} style={{ height: `${(count / peak) * 100}%` }} />
                    </div>
                    <span className={r.hour}>{hour % 3 === 0 ? hour : ""}</span>
                  </div>
                ))}
              </div>
            </section>
          </div>
        </>
      )}
    </>
  );
}
