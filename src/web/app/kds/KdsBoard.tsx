"use client";

import { useCallback, useEffect, useState } from "react";
import LangToggle from "@/components/LangToggle";
import { advanceOrder, AuthError, getBoard, type Board, type KdsOrder, type KdsStatus } from "@/lib/api";
import { setKdsToken } from "@/lib/kdsToken";
import { useLang } from "@/lib/useLang";
import styles from "./kds.module.css";

const STATUSES: KdsStatus[] = ["pending", "preparing", "ready"];
const POLL_MS = 4000; // ticket 06 replaces polling with the WebSocket

/** The KDS board: oldest new Order in focus on the start side, the queue on the end side. */
export default function KdsBoard({ token }: { token: string }) {
  const { lang, t, localized } = useLang();
  const [board, setBoard] = useState<Board | null>(null);
  const [offline, setOffline] = useState(false);
  const [notice, setNotice] = useState(false);
  const [busy, setBusy] = useState<string | null>(null);
  const now = useNow();

  /** The one place the board is fetched. */
  const loadBoard = useCallback(async () => {
    try {
      setBoard(await getBoard(token));
      setOffline(false);
    } catch (e) {
      if (e instanceof AuthError) setKdsToken(null);
      else setOffline(true);
    }
  }, [token]);

  useEffect(() => {
    const id = setInterval(loadBoard, POLL_MS);
    const first = setTimeout(loadBoard, 0);
    return () => {
      clearInterval(id);
      clearTimeout(first);
    };
  }, [loadBoard]);

  async function advance(order: KdsOrder) {
    setBusy(order.id);
    setNotice(false);
    try {
      if (!(await advanceOrder(token, order.id, order.status))) setNotice(true);
    } catch (e) {
      if (e instanceof AuthError) return setKdsToken(null);
      setOffline(true);
    } finally {
      setBusy(null);
    }
    await loadBoard();
  }

  const pickup = (o: KdsOrder) =>
    o.pickup_type === "table"
      ? `🪑 ${t("menu.table", { table: o.table_number ?? "" })}`
      : `🚗 ${[o.car_model, o.car_color, o.car_plate].join(" · ")}`;
  const ago = (o: KdsOrder) => {
    const minutes = Math.floor((now - Date.parse(o.paid_at ?? o.created_at)) / 60000);
    return minutes < 1 ? t("kds.justNow") : t("kds.minutesAgo", { n: minutes });
  };

  const orders = board?.orders ?? [];
  const focus = orders.find((o) => o.status === "pending");
  const clock = new Date(now).toLocaleTimeString(lang === "ar" ? "ar-SA-u-nu-latn" : "en-GB", {
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
  });

  return (
    <main className={styles.kds}>
      <header className={styles.bar}>
        <span className={styles.clock}>{clock}</span>
        {board && <b className={`serif ${styles.cafe}`}>{localized(board.cafe.name_ar, board.cafe.name_en)}</b>}
        {STATUSES.map((s) => (
          <span key={s} className={styles.count}>
            {t(`kds.count.${s}`)} <b>{orders.filter((o) => o.status === s).length}</b>
          </span>
        ))}
        <LangToggle />
        <button className={styles.logout} onClick={() => setKdsToken(null)}>
          {t("kds.logout")}
        </button>
      </header>

      {(offline || notice) && (
        <p className={styles.banner} role="alert">
          {t(offline ? "kds.error" : "kds.moved")}
        </p>
      )}

      {!board ? (
        <p className={styles.empty}>{t("common.loading")}</p>
      ) : (
        <div className={styles.split}>
          <section className={styles.now} aria-label={t("kds.focus")}>
            {focus ? (
              <>
                <span className={styles.tag}>● {t("kds.newOrder", { ago: ago(focus) })}</span>
                <div className={`serif ${styles.bigNumber}`}>#{focus.order_number}</div>
                <div className={styles.who}>
                  {focus.customer_name} · {pickup(focus)}
                </div>
                <ul className={styles.lines}>
                  {focus.lines.map((l, i) => (
                    <li key={i}>
                      {l.qty}× {localized(l.name_ar, l.name_en)}
                      {l.note && <small>{l.note}</small>}
                    </li>
                  ))}
                </ul>
                <button className={styles.accept} disabled={busy === focus.id} onClick={() => advance(focus)}>
                  {t("kds.acceptOrder")}
                </button>
              </>
            ) : (
              <p className={styles.empty}>{t("kds.noPending")}</p>
            )}
          </section>

          <section className={styles.queue}>
            {STATUSES.map((s) => {
              const group = orders.filter((o) => o.status === s && o !== focus);
              return (
                <div key={s}>
                  <h2>{t(`kds.group.${s}`)}</h2>
                  {group.length === 0 && <p className={styles.none}>—</p>}
                  {group.map((o) => (
                    <div key={o.id} className={styles.row}>
                      <span className={`serif ${styles.number}`}>#{o.order_number}</span>
                      <div className={styles.text}>
                        {o.lines.map((l, i) => (
                          <span key={i}>
                            {i > 0 && (lang === "ar" ? "، " : ", ")}
                            {l.qty}× {localized(l.name_ar, l.name_en)}
                            {l.note && <em className={styles.note}> ({l.note})</em>}
                          </span>
                        ))}
                        <small>
                          {o.customer_name} · {pickup(o)}
                        </small>
                      </div>
                      <button
                        className={styles.step}
                        data-status={s}
                        disabled={busy === o.id}
                        onClick={() => advance(o)}
                      >
                        {t(`kds.action.${s}`)}
                      </button>
                    </div>
                  ))}
                </div>
              );
            })}
          </section>
        </div>
      )}
    </main>
  );
}

/** Current time in ms, refreshed every 15 seconds for the clock and "minutes ago". */
function useNow() {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 15000);
    return () => clearInterval(id);
  }, []);
  return now;
}
