"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import LangToggle from "@/components/LangToggle";
import { payOrder, type Order, type PaymentMethod } from "@/lib/api";
import { clearCart } from "@/lib/cart";
import { useLang } from "@/lib/useLang";
import styles from "../../../order.module.css";

/** Fake payment page: Apple Pay and mada succeed, "simulate failure" declines. */
export default function PayView({ order }: { order: Order }) {
  const { t, localized, formatPrice } = useLang();
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<"failed" | "error" | null>(null);

  async function pay(method: PaymentMethod, source: "ok" | "fail" = "ok") {
    setBusy(true);
    setError(null);
    try {
      const paid = await payOrder(order.id, method, source);
      if (!paid) {
        setError("failed");
        return;
      }
      clearCart(order.cafe.slug);
      router.replace(`/o/${order.id}`);
    } catch {
      setError("error");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className={styles.page}>
      <header className={styles.hdr}>
        <h1 className="serif">{t("pay.title")}</h1>
        <LangToggle className={styles.lang} />
      </header>

      <section className={styles.box}>
        <h2>{localized(order.cafe.name_ar, order.cafe.name_en)}</h2>
        <div className={styles.row}>
          <span>{t("pay.amount")}</span>
          <b>{formatPrice(order.total)}</b>
        </div>
      </section>
      <p className={styles.hint}>{t("pay.demo")}</p>

      {error && (
        <p className={styles.error} role="alert">
          {t(error === "failed" ? "pay.failed" : "pay.error")}
        </p>
      )}

      <button className={`${styles.pay} ${styles.applePay}`} disabled={busy} onClick={() => pay("apple_pay")}>
        {t("pay.applePay")}
      </button>
      <button className={`${styles.pay} ${styles.mada}`} disabled={busy} onClick={() => pay("mada")}>
        {t("pay.mada")}
      </button>
      <button className={styles.link} disabled={busy} onClick={() => pay("mada", "fail")}>
        {t("pay.simulateFailure")}
      </button>
    </main>
  );
}
