import manifest from "@/app/manifest";

/** The Café's own manifest, so "Add to Home Screen" from its menu opens that Café, not the default one. */
export async function GET(_req: Request, { params }: RouteContext<"/c/[slug]/manifest.webmanifest">) {
  const { slug } = await params;
  const start = `/c/${encodeURIComponent(slug)}`;
  return Response.json(
    { ...manifest(), id: start, start_url: start, scope: "/" },
    { headers: { "Content-Type": "application/manifest+json" } },
  );
}
