import type { Metadata, Viewport } from "next";
import { Amiri, IBM_Plex_Sans_Arabic } from "next/font/google";
import { t } from "@/lib/i18n";
import "./globals.css";

const plex = IBM_Plex_Sans_Arabic({
  variable: "--font-plex",
  subsets: ["arabic", "latin"],
  weight: ["400", "500", "600", "700"],
});

const amiri = Amiri({
  variable: "--font-amiri",
  subsets: ["arabic", "latin"],
  weight: "700",
});

export const metadata: Metadata = {
  title: t("app.name"),
  description: t("app.description"),
  appleWebApp: { capable: true, title: t("app.name"), statusBarStyle: "default" },
};

export const viewport: Viewport = {
  themeColor: "#f7f0e6",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="ar" dir="rtl" className={`${plex.variable} ${amiri.variable}`}>
      <body>{children}</body>
    </html>
  );
}
