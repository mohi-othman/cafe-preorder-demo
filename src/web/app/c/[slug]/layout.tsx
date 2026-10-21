import type { Metadata } from "next";
import type { ReactNode } from "react";

/** Pages under /c/<slug> link the Café's own manifest instead of the app-wide one. */
export async function generateMetadata({ params }: LayoutProps<"/c/[slug]">): Promise<Metadata> {
  const { slug } = await params;
  return { manifest: `/c/${encodeURIComponent(slug)}/manifest.webmanifest` };
}

export default function Layout({ children }: { children: ReactNode }) {
  return children;
}
