import type { Metadata, Viewport } from "next";
import { t } from "@/lib/i18n";
import KdsApp from "./KdsApp";

export const metadata: Metadata = { title: t("kds.title") };
export const viewport: Viewport = { themeColor: "#3b2a1e" };

export default function Page() {
  return <KdsApp />;
}
