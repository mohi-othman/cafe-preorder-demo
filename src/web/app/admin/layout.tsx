import type { Metadata } from "next";
import { t } from "@/lib/i18n";
import AdminShell from "./AdminShell";

export const metadata: Metadata = { title: t("admin.title") };

/** Every /admin page renders inside the shell; pages read the token and Café with useAdmin(). */
export default function AdminLayout({ children }: LayoutProps<"/admin">) {
  return <AdminShell>{children}</AdminShell>;
}
