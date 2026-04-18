const PYTHON_BACKEND_URL =
  process.env.PYTHON_BACKEND_URL || "http://localhost:8000";

export async function POST() {
  try {
    const res = await fetch(`${PYTHON_BACKEND_URL}/api/icerikleri-guncelle`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });
    const data = await res.json();
    return Response.json(data);
  } catch (e) {
    return Response.json(
      { status: "error", message: String(e) },
      { status: 502 }
    );
  }
}
