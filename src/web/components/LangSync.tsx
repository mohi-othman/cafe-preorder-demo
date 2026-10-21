"use client";

import { useLayoutEffect } from "react";
import { applyLang, readStoredLang, useLang } from "@/lib/useLang";

/**
 * Keeps `<html lang dir>` in step with the chosen language and reveals the page
 * once React shows the saved language (the head script hides it until then).
 */
export default function LangSync() {
  const { lang } = useLang();
  useLayoutEffect(() => {
    // During hydration React first renders the server's Arabic; wait for the saved value.
    if (lang !== readStoredLang()) return;
    applyLang(lang);
    delete document.documentElement.dataset.langPending;
  }, [lang]);
  return null;
}
