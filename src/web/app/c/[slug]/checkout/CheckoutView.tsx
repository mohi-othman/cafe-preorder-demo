"use client";

import { useState, useSyncExternalStore } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { createOrder, type PickupType } from "@/lib/api";
import { useCart } from "@/lib/cart";
import { formatPrice, localized, t } from "@/lib/i18n";
import styles from "../../../order.module.css";

const noop = () => () => {};

export default function CheckoutView({ slug, table }: { slug: string; table: string | null }) {
  const router = useRouter();
  const cart = useCart(slug);
  // The cart lives in localStorage, so wait for the client before showing "empty".
  const hydrated = useSyncExternalStore(noop, () => true, () => false);
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [pickup, setPickup] = useState<PickupType>(table ? "table" : "car");
  const [tableNumber, setTableNumber] = useState(table ?? "");
  const [car, setCar] = useState({ model: "", color: "", plate: "" });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(false);

  const menuHref = `/c/${encodeURIComponent(slug)}${table ? `?table=${encodeURIComponent(table)}` : ""}`;

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(false);
    try {
      const order = await createOrder(slug, {
        customer_name: name.trim(),
        phone: phone.trim() || null,
        pickup_type: pickup,
        table_number: pickup === "table" ? tableNumber.trim() : null,
        car_model: pickup === "car" ? car.model.trim() : null,
        car_color: pickup === "car" ? car.color.trim() : null,
        car_plate: pickup === "car" ? car.plate.trim() : null,
        lines: cart.lines.map((l) => ({ product_id: l.product.id, qty: l.qty, note: l.note.trim() || null })),
      });
      router.push(`/o/${order.id}/pay`);
    } catch {
      setError(true);
    } finally {
      setBusy(false);
    }
  }

  const header = (
    <header className={styles.hdr}>
      <Link className={styles.back} href={menuHref} aria-label={t("checkout.back")}>
        →
      </Link>
      <h1 className="serif">{t("checkout.title")}</h1>
    </header>
  );

  if (!hydrated) return <p className={styles.status}>{t("common.loading")}</p>;

  if (cart.lines.length === 0) {
    return (
      <main className={styles.page}>
        {header}
        <p className={styles.status}>{t("checkout.empty")}</p>
        <Link className={styles.cta} href={menuHref}>
          {t("checkout.back")}
        </Link>
      </main>
    );
  }

  return (
    <main className={styles.page}>
      {header}
      <form onSubmit={submit}>
        <section className={styles.box}>
          <h2>{t("checkout.lines")}</h2>
          {cart.lines.map((l) => {
            const productName = localized(l.product.name_ar, l.product.name_en);
            return (
              <div key={l.product.id} className={styles.line}>
                <div className={styles.row}>
                  <span>{productName}</span>
                  <span>{formatPrice(l.product.price * l.qty)}</span>
                </div>
                <div className={styles.row}>
                  <input
                    className={styles.field}
                    placeholder={t("checkout.notePlaceholder")}
                    aria-label={t("checkout.note")}
                    maxLength={140}
                    value={l.note}
                    onChange={(e) => cart.setNote(l.product.id, e.target.value)}
                  />
                  <div className={styles.stepper}>
                    <button
                      type="button"
                      aria-label={t("checkout.decrease", { name: productName })}
                      onClick={() => cart.setQty(l.product.id, l.qty - 1)}
                    >
                      −
                    </button>
                    <b>{l.qty}</b>
                    <button
                      type="button"
                      aria-label={t("checkout.increase", { name: productName })}
                      onClick={() => cart.setQty(l.product.id, Math.min(99, l.qty + 1))}
                    >
                      +
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </section>

        <section className={styles.box}>
          <h2>{t("checkout.details")}</h2>
          <input
            className={styles.field}
            placeholder={t("checkout.name")}
            aria-label={t("checkout.name")}
            autoComplete="name"
            required
            maxLength={60}
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <input
            className={styles.field}
            type="tel"
            placeholder={t("checkout.phone")}
            aria-label={t("checkout.phone")}
            autoComplete="tel"
            maxLength={20}
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
          />
        </section>

        <section className={styles.box}>
          <h2>{t("checkout.pickup")}</h2>
          <div className={styles.seg} role="group" aria-label={t("checkout.pickup")}>
            <button type="button" aria-pressed={pickup === "table"} onClick={() => setPickup("table")}>
              🪑 {t("pickup.table")}
            </button>
            <button type="button" aria-pressed={pickup === "car"} onClick={() => setPickup("car")}>
              🚗 {t("pickup.car")}
            </button>
          </div>
          {pickup === "table" ? (
            <input
              className={styles.field}
              inputMode="numeric"
              placeholder={t("checkout.tableNumber")}
              aria-label={t("checkout.tableNumber")}
              required
              maxLength={10}
              value={tableNumber}
              onChange={(e) => setTableNumber(e.target.value)}
            />
          ) : (
            <>
              <input
                className={styles.field}
                placeholder={t("checkout.carModel")}
                aria-label={t("checkout.carModel")}
                required
                maxLength={80}
                value={car.model}
                onChange={(e) => setCar({ ...car, model: e.target.value })}
              />
              <input
                className={styles.field}
                placeholder={t("checkout.carColor")}
                aria-label={t("checkout.carColor")}
                required
                maxLength={80}
                value={car.color}
                onChange={(e) => setCar({ ...car, color: e.target.value })}
              />
              <input
                className={styles.field}
                placeholder={t("checkout.carPlate")}
                aria-label={t("checkout.carPlate")}
                required
                maxLength={80}
                value={car.plate}
                onChange={(e) => setCar({ ...car, plate: e.target.value })}
              />
            </>
          )}
        </section>

        <div className={styles.total}>
          <span>{t("checkout.total")}</span>
          <span>{formatPrice(cart.total)}</span>
        </div>
        <p className={styles.hint}>{t("checkout.vat")}</p>

        {error && (
          <p className={styles.error} role="alert">
            {t("checkout.error")}
          </p>
        )}
        <button className={styles.cta} type="submit" disabled={busy}>
          {t("checkout.submit")}
        </button>
      </form>
    </main>
  );
}
