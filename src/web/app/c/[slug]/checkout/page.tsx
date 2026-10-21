import { Suspense } from "react";
import T from "@/components/T";
import CheckoutView from "./CheckoutView";
import styles from "../../../order.module.css";

async function Checkout({ params, searchParams }: PageProps<"/c/[slug]/checkout">) {
  const { slug } = await params;
  const { table } = await searchParams;
  return <CheckoutView slug={slug} table={typeof table === "string" ? table : null} />;
}

export default function Page(props: PageProps<"/c/[slug]/checkout">) {
  return (
    <Suspense fallback={<p className={styles.status}><T k="common.loading" /></p>}>
      <Checkout {...props} />
    </Suspense>
  );
}
