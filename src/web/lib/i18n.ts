import ar from "./dictionaries/ar.json";
import en from "./dictionaries/en.json";

export type Lang = "ar" | "en";
export type Key = keyof typeof ar;

const dictionaries: Record<Lang, Record<Key, string>> = { ar, en };

/** Look up a UI string and fill `{name}` placeholders. Arabic is the default. */
export function t(key: Key, vars: Record<string, string | number> = {}, lang: Lang = "ar"): string {
  const text = dictionaries[lang][key] ?? dictionaries.ar[key];
  return text.replace(/\{(\w+)\}/g, (_, name: string) => String(vars[name] ?? `{${name}}`));
}

/** Pick the Arabic or English field of a record; empty English falls back to Arabic. */
export function localized(ar: string, en: string | null | undefined, lang: Lang = "ar"): string {
  return lang === "en" && en ? en : ar;
}

/** Halalas to a display price, e.g. 1850 -> "18.50 ر.س". */
export function formatPrice(halalas: number, lang: Lang = "ar"): string {
  const amount = halalas % 100 === 0 ? String(halalas / 100) : (halalas / 100).toFixed(2);
  return t("money.sar", { amount }, lang);
}
