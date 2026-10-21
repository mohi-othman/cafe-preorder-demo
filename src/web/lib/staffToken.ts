import { useSyncExternalStore } from "react";

export type StaffRole = "admin" | "barista";

/** Staff login tokens, one per role, kept in localStorage so a reload stays logged in. */
const KEYS: Record<StaffRole, string> = { admin: "qahwati.adminToken", barista: "qahwati.kdsToken" };
const listeners = new Set<() => void>();
const fallback: Record<StaffRole, string | null> = { admin: null, barista: null }; // when localStorage is blocked

function read(role: StaffRole): string | null {
  try {
    return localStorage.getItem(KEYS[role]);
  } catch {
    return fallback[role];
  }
}

export function setStaffToken(role: StaffRole, token: string | null) {
  fallback[role] = token;
  try {
    if (token) localStorage.setItem(KEYS[role], token);
    else localStorage.removeItem(KEYS[role]);
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

/** The role's token, null when logged out, or undefined while rendering on the server (not known yet). */
export function useStaffToken(role: StaffRole): string | null | undefined {
  return useSyncExternalStore<string | null | undefined>(subscribe, () => read(role), () => undefined);
}
