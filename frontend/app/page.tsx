import { ChangelogArticle } from "@/components/landing/ChangelogArticle";
import { LandingLayout } from "@/components/landing/Layout";

const PYTHON_BACKEND_URL =
  process.env.PYTHON_BACKEND_URL || "http://localhost:8000";

type ContentItem = {
  resim_url: string;
  baslik: string;
  tarih: string;
  ozet: string;
  kaynak_url: string;
  tur: "duyuru" | "haber";
};

const TR_MONTHS: Record<string, number> = {
  Oca: 1, Şub: 2, Mar: 3, Nis: 4, May: 5, Haz: 6,
  Tem: 7, Ağu: 8, Eyl: 9, Eki: 10, Kas: 11, Ara: 12,
};

function parseTurkishDate(s: string): Date {
  try {
    const [day, month, year] = s.trim().split(" ");
    return new Date(Number(year), (TR_MONTHS[month] ?? 1) - 1, Number(day));
  } catch {
    return new Date(0);
  }
}

function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "")
    .slice(0, 60);
}

async function fetchLatestItems(): Promise<ContentItem[]> {
  try {
    const [dRes, hRes] = await Promise.all([
      fetch(`${PYTHON_BACKEND_URL}/api/duyurular`, { cache: "no-store" }),
      fetch(`${PYTHON_BACKEND_URL}/api/haberler`, { cache: "no-store" }),
    ]);
    const duyurular: ContentItem[] = await dRes.json();
    const haberler: ContentItem[] = await hRes.json();

    const merged = [
      ...(Array.isArray(duyurular) ? duyurular : []),
      ...(Array.isArray(haberler) ? haberler : []),
    ];

    merged.sort(
      (a, b) =>
        parseTurkishDate(b.tarih).getTime() -
        parseTurkishDate(a.tarih).getTime(),
    );

    return merged.slice(0, 5);
  } catch {
    return [];
  }
}

export default async function LandingPage() {
  const items = await fetchLatestItems();

  return (
    <LandingLayout>
      {items.map((item) => (
        <ChangelogArticle
          key={item.kaynak_url}
          id={slugify(item.baslik)}
          date={parseTurkishDate(item.tarih).toISOString()}
        >
          <div className="relative overflow-hidden rounded-xl bg-gray-50 dark:bg-gray-900">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={item.resim_url}
              alt={item.baslik}
              className="w-full"
            />
            <div className="pointer-events-none absolute inset-0 rounded-xl ring-1 ring-gray-900/10 ring-inset dark:ring-white/10" />
          </div>
          <h2>{item.baslik}</h2>
          <p>{item.ozet}</p>
        </ChangelogArticle>
      ))}

      {items.length === 0 && (
        <p className="mx-auto max-w-lg py-20 text-center text-gray-500">
          Henüz içerik yüklenemedi. Backend sunucusunun çalıştığından emin olun.
        </p>
      )}
    </LandingLayout>
  );
}
