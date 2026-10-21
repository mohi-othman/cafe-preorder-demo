import { useSyncExternalStore } from "react";

/** The Barista's login token, kept in localStorage so a tablet reload stays logged in. */
const KEY = "qahwati.kdsToken";
const listeners = new Set<() => void>();
let fallback: string | null = null; // used when localStorage is blocked

function read(): string | null {
  try {
    return localStorage.getItem(KEY);
  } catch {
    return fallback;
  }
}

export function setKdsToken(token: string | null) {
  fallback = token;
  try {
    if (token) localStorage.setItem(KEY, token);
    else localStorage.removeItem(KEY);
  } catch {}
  listeners.forEach((l) => l());
}

function subscribe(listener: () => void) {
  listeners.add(listener);
  window.addEventListener("storage", listener);
  return () => {
    listeners.delete(listener);
    window.removeEventListener("storage", listener);
  };
}

/** The token, null when logged out, or undefined while rendering on the server (not known yet). */
export function useKdsToken(): string | null | undefined {
  return useSyncExternalStore<string | null | undefined>(subscribe, read, () => undefined);
}
