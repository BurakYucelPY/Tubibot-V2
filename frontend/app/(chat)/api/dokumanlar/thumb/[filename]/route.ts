const PYTHON_BACKEND_URL =
  process.env.PYTHON_BACKEND_URL || "http://localhost:8000";

export async function GET(
  _req: Request,
  { params }: { params: Promise<{ filename: string }> },
) {
  const { filename } = await params;
  const upstream = await fetch(
    `${PYTHON_BACKEND_URL}/api/dokumanlar/thumb/${encodeURIComponent(filename)}`,
    { cache: "no-store" },
  );
  if (!upstream.ok || !upstream.body) {
    return new Response("Not found", { status: 404 });
  }
  return new Response(upstream.body, {
    headers: {
      "Content-Type": "image/jpeg",
      "Cache-Control": "public, max-age=86400",
    },
  });
}
