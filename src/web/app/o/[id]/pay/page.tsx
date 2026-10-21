import { Suspense } from "react";
import { notFound, redirect } from "next/navigation";
import T from "@/components/T";
import { getOrder } from "@/lib/api";
import PayView from "./PayView";
import styles from "../../../order.module.css";

async function Pay({ params }: PageProps<"/o/[id]/pay">) {
  const { id } = await params;
  const order = await getOrder(id);
  if (!order) notFound();
  if (order.status !== "awaiting_payment") redirect(`/o/${order.id}`);
  return <PayView order={order} />;
}

export default function Page(props: PageProps<"/o/[id]/pay">) {
  return (
    <Suspense fallback={<p className={styles.status}><T k="common.loading" /></p>}>
      <Pay {...props} />
    </Suspense>
  );
}
