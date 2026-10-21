import { useEffect, useEffectEvent } from "react";
import { API_URL, type Order } from "./api";

/** Live events from the API's WebSocket; `order` has the same shape as the REST endpoints return. */
export type LiveEvent = { type: "order_created" | "status_changed"; order: Order };

/** The ws:// (or wss://) URL for an API path, derived from NEXT_PUBLIC_API_URL. */
export function wsUrl(path: string): string {
  return API_URL.replace(/^http/, "ws") + path;
}

const MAX_BACKOFF_MS = 15000;

/**
 * Keep a WebSocket open to `path` (no socket while it is null), reconnecting with backoff after drops.
 * `onOpen` runs on every (re)connect, so the caller can reload current state; `onClose` on every drop.
 */
export function useLiveSocket(
  path: string | null,
  handlers: { onEvent: (e: LiveEvent) => void; onOpen?: () => void; onClose?: () => void },
) {
  const onEvent = useEffectEvent(handlers.onEvent);
  const onOpen = useEffectEvent(() => handlers.onOpen?.());
  const onClose = useEffectEvent(() => handlers.onClose?.());

  useEffect(() => {
    if (!path) return;
    let socket: WebSocket | null = null;
    let retry: ReturnType<typeof setTimeout> | undefined;
    let backoff = 1000;
    let stopped = false;

    function connect() {
      socket = new WebSocket(wsUrl(path!));
      socket.onopen = () => {
        backoff = 1000;
        onOpen();
      };
      socket.onmessage = (m) => {
        try {
          onEvent(JSON.parse(m.data) as LiveEvent);
        } catch {}
      };
      socket.onclose = () => {
        if (stopped) return;
        onClose();
        retry = setTimeout(connect, backoff);
        backoff = Math.min(backoff * 2, MAX_BACKOFF_MS);
      };
    }

    connect();
    return () => {
      stopped = true;
      clearTimeout(retry);
      socket?.close();
    };
  }, [path]);
}
