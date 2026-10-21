import { Suspense } from "react";
import { notFound } from "next/navigation";
import T from "@/components/T";
import { getOrder } from "@/lib/api";
import OrderView from "./OrderView";
import styles from "../../order.module.css";

async function Tracking({ params }: PageProps<"/o/[id]">) {
  const { id } = await params;
  const order = await getOrder(id);
  if (!order) notFound();
  return <OrderView order={order} />;
}

export default function Page(props: PageProps<"/o/[id]">) {
  return (
    <Suspense fallback={<p className={styles.status}><T k="common.loading" /></p>}>
      <Tracking {...props} />
    </Suspense>
  );
}
