"use client";

import StaffLogin from "@/components/StaffLogin";
import { useStaffToken } from "@/lib/staffToken";
import KdsBoard from "./KdsBoard";
import styles from "./kds.module.css";

/** /kds: the login form, then the board. */
export default function KdsApp() {
  const token = useStaffToken("barista");
  if (token === undefined) return null; // server render: the token lives in the browser
  return token ? <KdsBoard token={token} /> : <StaffLogin role="barista" styles={styles} />;
}
