"use client";

import { useCallback, useSyncExternalStore } from "react";
import { formatPrice, langStorageKey, localized, t, type Key, type Lang } from "./i18n";

const CHANGE_EVENT = "langchange";
let fallback: Lang = "ar"; // used when localStorage is blocked

/** Saved choice; Arabic when nothing is stored. */
export function readStoredLang(): Lang {
  try {
    return localStorage.getItem(langStorageKey(location.pathname)) === "en" ? "en" : "ar";
  } catch {
    return fallback;
  }
}

/** Point `<html lang dir>` at the language. */
export function applyLang(lang: Lang) {
  const html = document.documentElement;
  html.lang = lang;
  html.dir = lang === "ar" ? "rtl" : "ltr";
}

function subscribe(onChange: () => void) {
  window.addEventListener(CHANGE_EVENT, onChange);
  window.addEventListener("storage", onChange);
  return () => {
    window.removeEventListener(CHANGE_EVENT, onChange);
    window.removeEventListener("storage", onChange);
  };
}

export function setLang(lang: Lang) {
  fallback = lang;
  try {
    localStorage.setItem(langStorageKey(location.pathname), lang);
  } catch {
    // Storage blocked: the switch still works until reload.
  }
  applyLang(lang);
  window.dispatchEvent(new Event(CHANGE_EVENT));
}

/**
 * Current UI language plus helpers bound to it. The server renders Arabic;
 * the client switches to the saved language right after hydration.
 */
export function useLang() {
  const lang = useSyncExternalStore<Lang>(subscribe, readStoredLang, () => "ar");
  return {
    lang,
    setLang,
    t: useCallback((key: Key, vars?: Record<string, string | number>) => t(key, vars, lang), [lang]),
    localized: useCallback((ar: string, en: string | null | undefined) => localized(ar, en, lang), [lang]),
    formatPrice: useCallback((halalas: number) => formatPrice(halalas, lang), [lang]),
  };
}
