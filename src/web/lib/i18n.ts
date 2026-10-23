import ar from "./dictionaries/ar.json";
import en from "./dictionaries/en.json";

export type Lang = "ar" | "en";
export type Key = keyof typeof ar;

/** localStorage key holding the chosen language. Staff pages keep their own, apart from customers. */
export const LANG_STORAGE_KEY = "lang";
export const STAFF_LANG_STORAGE_KEY = "lang.staff";
export const STAFF_PATH = /^\/(kds|admin)(\/|$)/;

export function langStorageKey(pathname: string): string {
  return STAFF_PATH.test(pathname) ? STAFF_LANG_STORAGE_KEY : LANG_STORAGE_KEY;
}

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
