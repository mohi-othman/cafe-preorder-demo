"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import LangToggle from "@/components/LangToggle";
import { AuthError } from "@/lib/api";
import { listCafes, type AdminCafe } from "@/lib/adminApi";
import { setAdminToken, useAdminToken } from "@/lib/adminToken";
import type { Key } from "@/lib/i18n";
import { useLang } from "@/lib/useLang";
import AdminLogin from "./AdminLogin";
import styles from "./admin.module.css";

type AdminContextValue = {
  token: string;
  cafes: AdminCafe[];
  /** The Café picked in the sidebar; null when there are no Cafés. */
  cafe: AdminCafe | null;
  /** Fetch the Café list again (e.g. after adding a Café). */
  reloadCafes: () => Promise<void>;
  /** Call with any error from lib/adminApi: logs out on AuthError, else returns false. */
  handleAuthError: (e: unknown) => boolean;
};

const AdminContext = createContext<AdminContextValue | null>(null);

/** Token, Cafés and the picked Café for pages under /admin. */
export function useAdmin(): AdminContextValue {
  const value = useContext(AdminContext);
  if (!value) throw new Error("useAdmin() outside the admin layout");
  return value;
}

const NAV: { href: string; label: Key }[] = [
  { href: "/admin/cafes", label: "admin.nav.cafes" },
  { href: "/admin/menu", label: "admin.nav.menu" },
  { href: "/admin/reports", label: "admin.nav.reports" },
  { href: "/admin/qr", label: "admin.nav.qr" },
];

/** /admin: the login form, then the ink sidebar with the Café picker around each admin page. */
export default function AdminShell({ children }: { children: ReactNode }) {
  const token = useAdminToken();
  if (token === undefined) return null; // server render: the token lives in the browser
  return token ? <AdminFrame token={token}>{children}</AdminFrame> : <AdminLogin />;
}

function handleAuthError(e: unknown) {
  if (!(e instanceof AuthError)) return false;
  setAdminToken(null);
  return true;
}

function AdminFrame({ token, children }: { token: string; children: ReactNode }) {
  const { t, localized } = useLang();
  const pathname = usePathname();
  const [cafes, setCafes] = useState<AdminCafe[] | null>(null);
  const [cafeId, setCafeId] = useState<number | null>(null);
  const [error, setError] = useState(false);

  const reloadCafes = useCallback(async () => {
    try {
      setCafes(await listCafes(token));
      setError(false);
    } catch (e) {
      if (!handleAuthError(e)) setError(true);
    }
  }, [token]);

  useEffect(() => {
    const id = setTimeout(reloadCafes, 0);
    return () => clearTimeout(id);
  }, [reloadCafes]);

  const cafe = cafes?.find((c) => c.id === cafeId) ?? cafes?.[0] ?? null;

  return (
    <div className={styles.shell}>
      <nav className={styles.side}>
        <div className={`serif ${styles.brand}`}>{t("admin.brand")}</div>
        {cafes && cafes.length > 0 && (
          <label className={styles.picker}>
            {t("admin.cafe")}
            <select value={cafe?.id ?? ""} onChange={(e) => setCafeId(Number(e.target.value))}>
              {cafes.map((c) => (
                <option key={c.id} value={c.id}>
                  {localized(c.name_ar, c.name_en)}
                </option>
              ))}
            </select>
          </label>
        )}
        {NAV.map((n) => (
          <Link key={n.href} href={n.href} className={pathname.startsWith(n.href) ? styles.on : undefined}>
            {t(n.label)}
          </Link>
        ))}
        <div className={styles.sideFoot}>
          <LangToggle />
          <button className={styles.logout} onClick={() => setAdminToken(null)}>
            {t("admin.logout")}
          </button>
        </div>
      </nav>
      <main className={styles.main}>
        {error && (
          <p className={styles.error} role="alert">
            {t("admin.error")}
          </p>
        )}
        {cafes && (
          <AdminContext.Provider value={{ token, cafes, cafe, reloadCafes, handleAuthError }}>
            {children}
          </AdminContext.Provider>
        )}
      </main>
    </div>
  );
}
