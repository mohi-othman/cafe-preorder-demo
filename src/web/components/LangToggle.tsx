"use client";

import { useLang } from "@/lib/useLang";
import styles from "./LangToggle.module.css";

/** Button that flips between Arabic and English. Drop it into any page header. */
export default function LangToggle({ className = "" }: { className?: string }) {
  const { lang, setLang, t } = useLang();
  const other = lang === "ar" ? "en" : "ar";
  return (
    <button
      type="button"
      className={`${styles.toggle} ${className}`}
      lang={other}
      aria-label={t("lang.switchLabel")}
      onClick={() => setLang(other)}
    >
      {t("lang.switch")}
    </button>
  );
}
