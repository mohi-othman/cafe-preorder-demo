"use client";

import Link from "next/link";
import LangToggle from "@/components/LangToggle";
import type { Order } from "@/lib/api";
import { useLang } from "@/lib/useLang";
import styles from "../../order.module.css";

/** Tracking page body: Order Number, status, pickup and Order Lines. Live updates come in ticket 06. */
export default function OrderView({ order }: { order: Order }) {
  const { t, localized, formatPrice } = useLang();
  const pickup =
    order.pickup_type === "table"
      ? `🪑 ${t("menu.table", { table: order.table_number ?? "" })}`
      : `🚗 ${[order.car_model, order.car_color, order.car_plate].join(" · ")}`;
  const menuHref =
    `/c/${encodeURIComponent(order.cafe.slug)}` +
    (order.table_number ? `?table=${encodeURIComponent(order.table_number)}` : "");

  return (
    <main className={styles.page}>
      <header className={styles.hdr}>
        <h1 className="serif">{localized(order.cafe.name_ar, order.cafe.name_en)}</h1>
        <LangToggle className={styles.lang} />
      </header>

      <section className={`${styles.box} ${styles.number}`}>
        {order.order_number !== null && (
          <>
            <small>{t("order.number")}</small>
            <strong className="serif">#{order.order_number}</strong>
          </>
        )}
        <span className={styles.pill} data-status={order.status} role="status">
          {t(`order.status.${order.status}`)}
        </span>
      </section>

      {order.status === "awaiting_payment" ? (
        <Link className={styles.cta} href={`/o/${order.id}/pay`}>
          {t("order.pay")}
        </Link>
      ) : (
        <p className={styles.hint}>{t("order.thanks", { name: order.customer_name })}</p>
      )}

      <section className={styles.box}>
        <h2>{t("checkout.lines")}</h2>
        {order.lines.map((l, i) => (
          <div key={i} className={styles.line}>
            <div className={styles.row}>
              <span>
                {l.qty}× {localized(l.name_ar, l.name_en)}
              </span>
              <span>{formatPrice(l.unit_price * l.qty)}</span>
            </div>
            {l.note && <div className={styles.note}>{l.note}</div>}
          </div>
        ))}
      </section>

      <section className={styles.box}>
        <h2>{t("checkout.pickup")}</h2>
        <div className={styles.row}>{pickup}</div>
      </section>

      <div className={styles.total}>
        <span>{t("checkout.total")}</span>
        <span>{formatPrice(order.total)}</span>
      </div>
      <p className={styles.hint}>{t("checkout.vat")}</p>

      <Link className={styles.link} href={menuHref}>
        {t("order.more")}
      </Link>
    </main>
  );
}
