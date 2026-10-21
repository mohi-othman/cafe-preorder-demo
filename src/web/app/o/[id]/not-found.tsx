import T from "@/components/T";
import styles from "../../order.module.css";

export default function NotFound() {
  return (
    <p className={styles.status}>
      <T k="order.notFound" />
    </p>
  );
}
