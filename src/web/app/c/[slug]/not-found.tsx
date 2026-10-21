import LangToggle from "@/components/LangToggle";
import T from "@/components/T";
import styles from "./menu.module.css";

export default function NotFound() {
  return (
    <main className={styles.page}>
      <header className={styles.top}>
        <LangToggle className={styles.lang} />
      </header>
      <p className={styles.status}>
        <T k="cafe.notFound" />
      </p>
    </main>
  );
}
