"use client";

import { useKdsToken } from "@/lib/kdsToken";
import KdsBoard from "./KdsBoard";
import KdsLogin from "./KdsLogin";

/** /kds: the login form, then the board. */
export default function KdsApp() {
  const token = useKdsToken();
  if (token === undefined) return null; // server render: the token lives in the browser
  return token ? <KdsBoard token={token} /> : <KdsLogin />;
}
