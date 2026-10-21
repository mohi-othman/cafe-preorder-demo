import { Suspense } from "react";
import { notFound } from "next/navigation";
import { getMenu } from "@/lib/api";
import { t } from "@/lib/i18n";
import MenuView from "./MenuView";
import styles from "./menu.module.css";

async function CafeMenu({ params, searchParams }: PageProps<"/c/[slug]">) {
  const { slug } = await params;
  const { table } = await searchParams;
  const menu = await getMenu(slug);
  if (!menu) notFound();
  return <MenuView menu={menu} table={typeof table === "string" ? table : null} />;
}

export default function Page(props: PageProps<"/c/[slug]">) {
  return (
    <Suspense fallback={<p className={styles.status}>{t("common.loading")}</p>}>
      <CafeMenu {...props} />
    </Suspense>
  );
}
