"use client";

import { useCallback, useEffect, useState } from "react";
import LangToggle from "@/components/LangToggle";
import {
  advanceOrder,
  AuthError,
  getBoard,
  type Board,
  type KdsOrder,
  type KdsStatus,
  type Order,
} from "@/lib/api";
import { setKdsToken } from "@/lib/kdsToken";
import { type LiveEvent, useLiveSocket } from "@/lib/live";
import { useLang } from "@/lib/useLang";
import { playChime, unlockAudio } from "./chime";
import styles from "./kds.module.css";

const STATUSES: KdsStatus[] = ["pending", "preparing", "ready"];
const FLASH_MS = 2500;

/** The KDS board: oldest new Order in focus on the start side, the queue on the end side. */
export default function KdsBoard({ token }: { token: string }) {
  const { lang, t, localized } = useLang();
  const [started, setStarted] = useState(false);
  const [board, setBoard] = useState<Board | null>(null);
  const [offline, setOffline] = useState(false);
  const [notice, setNotice] = useState(false);
  const [busy, setBusy] = useState<string | null>(null);
  const [flashing, setFlashing] = useState<ReadonlySet<string>>(new Set());
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

  function flash(id: string) {
    setFlashing((s) => new Set(s).add(id));
    setTimeout(
      () =>
        setFlashing((s) => {
          const next = new Set(s);
          next.delete(id);
          return next;
        }),
      FLASH_MS,
    );
  }

  // Live updates once the shift has started; every (re)connect reloads the board.
  useLiveSocket(started ? `/api/ws/kds?token=${encodeURIComponent(token)}` : null, {
    onOpen: loadBoard,
    // A drop: the reload logs out on a bad token, or shows the banner until the socket is back.
    onClose: () => void loadBoard().then(() => setOffline(true)),
    onEvent: ({ type, order }: LiveEvent) => {
      setBoard((b) => b && { ...b, orders: withOrder(b.orders, order) });
      if (type === "order_created") {
        playChime();
        flash(order.id);
      }
    },
  });

  function startShift() {
    unlockAudio();
    setStarted(true);
  }

  if (!started) {
    return (
      <main className={styles.start}>
        <LangToggle />
        <button className={styles.startButton} onClick={startShift}>
          {t("kds.startShift")}
        </button>
        <p>{t("kds.startShiftHint")}</p>
      </main>
    );
  }

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
          <section
            className={`${styles.now} ${focus && flashing.has(focus.id) ? styles.flash : ""}`}
            aria-label={t("kds.focus")}
          >
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
                    <div key={o.id} className={`${styles.row} ${flashing.has(o.id) ? styles.flash : ""}`}>
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

/** The board's Orders with `order` added, replaced, or removed once it has left the board; oldest paid first. */
function withOrder(orders: KdsOrder[], order: Order): KdsOrder[] {
  const rest = orders.filter((o) => o.id !== order.id);
  if (!STATUSES.includes(order.status as KdsStatus)) return rest;
  return [...rest, order as KdsOrder].sort((a, b) => (a.paid_at ?? "").localeCompare(b.paid_at ?? ""));
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
