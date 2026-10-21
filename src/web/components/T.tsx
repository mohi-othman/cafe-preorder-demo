"use client";

import type { Key } from "@/lib/i18n";
import { useLang } from "@/lib/useLang";

/** A UI string in the chosen language, for use inside Server Components. */
export default function T({ k, vars }: { k: Key; vars?: Record<string, string | number> }) {
  return useLang().t(k, vars);
}
