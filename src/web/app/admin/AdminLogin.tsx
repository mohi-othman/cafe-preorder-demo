"use client";

import { useState, type FormEvent } from "react";
import LangToggle from "@/components/LangToggle";
import { login } from "@/lib/api";
import { setAdminToken } from "@/lib/adminToken";
import { useLang } from "@/lib/useLang";
import styles from "./admin.module.css";

export default function AdminLogin() {
  const { t } = useLang();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<"admin.loginFailed" | "admin.notAdmin" | "admin.error" | null>(null);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const res = await login(username, password);
      if (!res) setError("admin.loginFailed");
      else if (res.role !== "admin") setError("admin.notAdmin");
      else setAdminToken(res.access_token);
    } catch {
      setError("admin.error");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className={styles.loginPage}>
      <form className={styles.loginBox} onSubmit={submit}>
        <div className={styles.loginHead}>
          <h1 className="serif">{t("admin.login")}</h1>
          <LangToggle />
        </div>
        <label>
          {t("admin.username")}
          <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
            autoCapitalize="none"
            required
          />
        </label>
        <label>
          {t("admin.password")}
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            required
          />
        </label>
        {error && (
          <p className={styles.error} role="alert">
            {t(error)}
          </p>
        )}
        <button className={styles.primary} disabled={busy}>
          {t("admin.signIn")}
        </button>
      </form>
    </main>
  );
}
