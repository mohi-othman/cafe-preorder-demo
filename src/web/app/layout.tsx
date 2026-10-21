import type { Metadata, Viewport } from "next";
import { Amiri, IBM_Plex_Sans_Arabic } from "next/font/google";
import LangSync from "@/components/LangSync";
import { LANG_STORAGE_KEY, t } from "@/lib/i18n";
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

// Runs before first paint: apply the saved English choice to <html> and hide the
// body until React renders English text (LangSync reveals it; 3s safety net).
const LANG_SCRIPT = `(function(){try{if(localStorage.getItem(${JSON.stringify(LANG_STORAGE_KEY)})!=="en")return;var h=document.documentElement;h.lang="en";h.dir="ltr";h.dataset.langPending="";setTimeout(function(){delete h.dataset.langPending},3000)}catch(e){}})()`;

export const viewport: Viewport = {
  themeColor: "#f7f0e6",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="ar" dir="rtl" className={`${plex.variable} ${amiri.variable}`} suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: LANG_SCRIPT }} />
      </head>
      <body>
        <LangSync />
        {children}
      </body>
    </html>
  );
}
