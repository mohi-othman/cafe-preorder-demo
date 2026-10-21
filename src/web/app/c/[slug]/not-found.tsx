import { t } from "@/lib/i18n";
import styles from "./menu.module.css";

export default function NotFound() {
  return <p className={styles.status}>{t("cafe.notFound")}</p>;
}
