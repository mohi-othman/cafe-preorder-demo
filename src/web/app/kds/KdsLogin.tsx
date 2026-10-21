"use client";

import { useState, type FormEvent } from "react";
import LangToggle from "@/components/LangToggle";
import { login } from "@/lib/api";
import { setKdsToken } from "@/lib/kdsToken";
import { useLang } from "@/lib/useLang";
import styles from "./kds.module.css";

export default function KdsLogin() {
  const { t } = useLang();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<"kds.loginFailed" | "kds.notBarista" | "kds.error" | null>(null);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const res = await login(username, password);
      if (!res) setError("kds.loginFailed");
      else if (res.role !== "barista") setError("kds.notBarista");
      else setKdsToken(res.access_token);
    } catch {
      setError("kds.error");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className={styles.loginPage}>
      <form className={styles.loginBox} onSubmit={submit}>
        <div className={styles.loginHead}>
          <h1 className="serif">{t("kds.login")}</h1>
          <LangToggle />
        </div>
        <label>
          {t("kds.username")}
          <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
            autoCapitalize="none"
            required
          />
        </label>
        <label>
          {t("kds.password")}
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
          {t("kds.signIn")}
        </button>
      </form>
    </main>
  );
}
