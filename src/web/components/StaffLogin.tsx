"use client";

import { useState, type FormEvent } from "react";
import LangToggle from "@/components/LangToggle";
import { login } from "@/lib/api";
import type { Key } from "@/lib/i18n";
import { setStaffToken, type StaffRole } from "@/lib/staffToken";
import { useLang } from "@/lib/useLang";

/** The texts each login form uses: the Super Admin's under "admin.", the Barista's under "kds.". */
const TEXTS = {
  admin: {
    title: "admin.login", username: "admin.username", password: "admin.password", signIn: "admin.signIn",
    failed: "admin.loginFailed", wrongRole: "admin.notAdmin", error: "admin.error",
  },
  barista: {
    title: "kds.login", username: "kds.username", password: "kds.password", signIn: "kds.signIn",
    failed: "kds.loginFailed", wrongRole: "kds.notBarista", error: "kds.error",
  },
} satisfies Record<StaffRole, Record<string, Key>>;

/** Username/password form that stores the token for `role`; other roles' logins are refused. */
export default function StaffLogin({ role, styles }: { role: StaffRole; styles: Record<string, string> }) {
  const { t } = useLang();
  const texts = TEXTS[role];
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<Key | null>(null);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const res = await login(username, password);
      if (!res) setError(texts.failed);
      else if (res.role !== role) setError(texts.wrongRole);
      else setStaffToken(role, res.access_token);
    } catch {
      setError(texts.error);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className={styles.loginPage}>
      <form className={styles.loginBox} onSubmit={submit}>
        <div className={styles.loginHead}>
          <h1 className="serif">{t(texts.title)}</h1>
          <LangToggle />
        </div>
        <label>
          {t(texts.username)}
          <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
            autoCapitalize="none"
            required
          />
        </label>
        <label>
          {t(texts.password)}
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
          {t(texts.signIn)}
        </button>
      </form>
    </main>
  );
}
