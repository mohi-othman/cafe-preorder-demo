import { useEffect, useEffectEvent } from "react";
import { API_URL, type Order } from "./api";

/** Live events from the API's WebSocket; `order` has the same shape as the REST endpoints return. */
export type LiveEvent = { type: "order_created" | "status_changed"; order: Order };

/** The ws:// (or wss://) URL for an API path, derived from NEXT_PUBLIC_API_URL. */
export function wsUrl(path: string): string {
  return API_URL.replace(/^http/, "ws") + path;
}

const MAX_BACKOFF_MS = 15000;
const UNAUTHORIZED = 4401; // the API's close code for a bad or expired token

/**
 * Keep a WebSocket open to `path` (no socket while it is null), reconnecting with backoff after drops.
 * With a `token`, it is sent as the first message (never in the URL).
 * `onOpen` runs once the API says the socket is subscribed, on every (re)connect, so the caller can reload
 * current state; `onClose` on every drop. On a 4401 close `onUnauthorized` runs and there is no reconnect.
 */
export function useLiveSocket(
  path: string | null,
  handlers: {
    token?: string;
    onEvent: (e: LiveEvent) => void;
    onOpen?: () => void;
    onClose?: () => void;
    onUnauthorized?: () => void;
  },
) {
  const { token } = handlers;
  const onEvent = useEffectEvent(handlers.onEvent);
  const onOpen = useEffectEvent(() => handlers.onOpen?.());
  const onClose = useEffectEvent(() => handlers.onClose?.());
  const onUnauthorized = useEffectEvent(() => handlers.onUnauthorized?.());

  useEffect(() => {
    if (!path) return;
    let socket: WebSocket | null = null;
    let retry: ReturnType<typeof setTimeout> | undefined;
    let backoff = 1000;
    let stopped = false;

    function connect() {
      socket = new WebSocket(wsUrl(path!));
      socket.onopen = () => {
        if (token) socket?.send(JSON.stringify({ token }));
      };
      socket.onmessage = (m) => {
        let message: { type?: string };
        try {
          message = JSON.parse(m.data);
        } catch {
          return;
        }
        if (message.type === "ready") {
          backoff = 1000;
          onOpen();
        } else {
          onEvent(message as LiveEvent);
        }
      };
      socket.onclose = (e) => {
        if (stopped) return;
        if (e.code === UNAUTHORIZED) {
          stopped = true;
          onUnauthorized();
          return;
        }
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
  }, [path, token]);
}
