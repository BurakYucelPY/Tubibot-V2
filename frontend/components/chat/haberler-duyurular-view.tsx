"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  ChevronLeftIcon,
  ChevronRightIcon,
  RefreshCwIcon,
  XIcon,
} from "lucide-react";

type Duyuru = {
  resim_url: string;
  baslik: string;
  tarih: string;
  ozet: string;
  kaynak_url: string;
  tam_icerik: string;
  tur: "duyuru" | "haber";
};

type FilterType = "hepsi" | "duyuru" | "haber";

const basePath = process.env.NEXT_PUBLIC_BASE_PATH ?? "";
const PER_PAGE = 18;

// Türkçe kısa ay isimleri → ay numarası (frontend'de sıralama için)
const TR_MONTHS: Record<string, number> = {
  Oca: 1, Şub: 2, Mar: 3, Nis: 4, May: 5, Haz: 6,
  Tem: 7, Ağu: 8, Eyl: 9, Eki: 10, Kas: 11, Ara: 12,
};

function parseTurkishDate(s: string): number {
  try {
    const [day, month, year] = s.trim().split(" ");
    return new Date(
      Number(year),
      (TR_MONTHS[month] ?? 1) - 1,
      Number(day)
    ).getTime();
  } catch {
    return 0;
  }
}

export function HaberlerDuyurularView() {
  const [items, setItems] = useState<Duyuru[]>([]);
  const [loading, setLoading] = useState(true);
  const [updateStatus, setUpdateStatus] = useState<
    "idle" | "loading" | "done" | "error"
  >("idle");
  const [errorMessage, setErrorMessage] = useState("");
  const [selectedItem, setSelectedItem] = useState<Duyuru | null>(null);
  const [filter, setFilter] = useState<FilterType>("hepsi");
  const [page, setPage] = useState(1);

  const fetchItems = useCallback(async () => {
    try {
      const [duyurularRes, haberlerRes] = await Promise.all([
        fetch(`${basePath}/api/duyurular`),
        fetch(`${basePath}/api/haberler`),
      ]);
      const duyurular: Duyuru[] = await duyurularRes.json();
      const haberler: Duyuru[] = await haberlerRes.json();

      const merged = [
        ...(Array.isArray(duyurular) ? duyurular : []),
        ...(Array.isArray(haberler) ? haberler : []),
      ];
      merged.sort((a, b) => parseTurkishDate(b.tarih) - parseTurkishDate(a.tarih));
      setItems(merged);
    } catch {
      // silently fail
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchItems();
  }, [fetchItems]);

  const handleUpdate = async () => {
    setUpdateStatus("loading");
    setErrorMessage("");
    try {
      const res = await fetch(`${basePath}/api/duyurulari-guncelle`, {
        method: "POST",
      });
      const data = await res.json();
      if (data.status === "ok") {
        setUpdateStatus("done");
        await fetchItems();
        setTimeout(() => setUpdateStatus("idle"), 3000);
      } else {
        setUpdateStatus("error");
        setErrorMessage(data.message || "Bilinmeyen hata");
      }
    } catch (e) {
      setUpdateStatus("error");
      setErrorMessage(String(e));
    }
  };

  // Filtrelenmiş içerikler
  const filtered = useMemo(
    () =>
      filter === "hepsi" ? items : items.filter((d) => d.tur === filter),
    [items, filter]
  );

  // Sayfalama
  const totalPages = Math.max(1, Math.ceil(filtered.length / PER_PAGE));
  const paged = useMemo(
    () => filtered.slice((page - 1) * PER_PAGE, page * PER_PAGE),
    [filtered, page]
  );

  // Filtre değişince sayfa 1'e dön
  const handleFilterChange = (f: FilterType) => {
    setFilter(f);
    setPage(1);
  };

  return (
    <div className="relative z-1 flex-1 overflow-y-auto pt-8 pb-16 sm:pt-10 sm:pb-20">
      <div className="mx-auto max-w-7xl px-6 lg:px-8">
        <div className="mx-auto flex max-w-2xl flex-col items-center">
          <h2 className="text-center font-semibold text-2xl tracking-tight text-foreground md:text-3xl">
            Haberler ve Duyurular
          </h2>
          <p className="mt-3 text-center text-muted-foreground/80 text-sm">
            TÜBİTAK gündeminden seçilmiş son haberler ve duyurular.
          </p>
        </div>

        {/* Güncelle Butonu + Filtreler */}
        <div className="mx-auto mt-6 flex max-w-2xl flex-col gap-4 lg:mx-0 lg:max-w-none lg:flex-row lg:items-center lg:justify-between">
          <div className="flex flex-col items-start">
            <button
              type="button"
              disabled={updateStatus === "loading"}
              onClick={handleUpdate}
              className="inline-flex items-center gap-2 rounded-lg bg-primary/10 px-4 py-2 text-sm font-medium text-primary transition-colors hover:bg-primary/20 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <RefreshCwIcon
                className={`size-4 ${updateStatus === "loading" ? "animate-spin" : ""}`}
              />
              {updateStatus === "idle" && "İçerikleri Güncelle"}
              {updateStatus === "loading" && "Yükleniyor..."}
              {updateStatus === "done" && "Tamamlandı \u2713"}
              {updateStatus === "error" && "İçerikleri Güncelle"}
            </button>
            {updateStatus === "error" && errorMessage && (
              <p className="mt-2 text-xs text-red-500">{errorMessage}</p>
            )}
          </div>

          {/* Filtre Butonları */}
          <div className="flex gap-2">
            {(
              [
                { key: "hepsi", label: "Hepsi" },
                { key: "duyuru", label: "Duyurular" },
                { key: "haber", label: "Haberler" },
              ] as const
            ).map((f) => (
              <button
                key={f.key}
                type="button"
                onClick={() => handleFilterChange(f.key)}
                className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
                  filter === f.key
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted text-muted-foreground hover:bg-muted/80"
                }`}
              >
                {f.label}
              </button>
            ))}
          </div>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="mx-auto mt-12 flex justify-center">
            <div className="size-8 animate-spin rounded-full border-2 border-muted-foreground/30 border-t-primary" />
          </div>
        )}

        {/* Boş State */}
        {!loading && items.length === 0 && (
          <p className="mx-auto mt-12 text-center text-muted-foreground text-sm">
            Henüz içerik yok. Yukarıdaki butona basarak içerikleri
            çekebilirsiniz.
          </p>
        )}

        {!loading && items.length > 0 && filtered.length === 0 && (
          <p className="mx-auto mt-12 text-center text-muted-foreground text-sm">
            Bu filtreye uygun içerik bulunamadı.
          </p>
        )}

        {/* Kartlar */}
        {!loading && paged.length > 0 && (
          <>
            <div className="mx-auto mt-12 grid max-w-2xl grid-cols-1 gap-x-8 gap-y-16 lg:mx-0 lg:max-w-none lg:grid-cols-3">
              {paged.map((item, i) => (
                <article
                  key={`${item.kaynak_url}-${i}`}
                  className="flex cursor-pointer flex-col items-start justify-between transition-opacity hover:opacity-80"
                  onClick={() => setSelectedItem(item)}
                >
                  <div className="relative w-full">
                    <img
                      alt={item.baslik}
                      src={item.resim_url}
                      className="aspect-video w-full rounded-2xl bg-muted object-contain sm:aspect-2/1 lg:aspect-3/2"
                    />
                    <div className="absolute inset-0 rounded-2xl inset-ring inset-ring-white/10" />
                  </div>
                  <div className="flex max-w-xl grow flex-col justify-between">
                    <div className="mt-8 flex items-center gap-x-4 text-xs">
                      <time className="text-muted-foreground">
                        {item.tarih}
                      </time>
                      <span
                        className={`rounded-full px-2.5 py-0.5 font-medium ${
                          item.tur === "duyuru"
                            ? "bg-blue-500/10 text-blue-400"
                            : "bg-emerald-500/10 text-emerald-400"
                        }`}
                      >
                        {item.tur === "duyuru" ? "Duyuru" : "Haber"}
                      </span>
                    </div>
                    <div className="group relative grow">
                      <h3 className="mt-3 text-lg/6 font-semibold text-foreground group-hover:text-muted-foreground">
                        {item.baslik}
                      </h3>
                      <p className="mt-5 line-clamp-3 text-sm/6 text-muted-foreground">
                        {item.ozet}
                      </p>
                    </div>
                  </div>
                </article>
              ))}
            </div>

            {/* Sayfalama */}
            {totalPages > 1 && (
              <Pagination
                current={page}
                total={totalPages}
                onChange={setPage}
              />
            )}
          </>
        )}
      </div>

      {/* Modal */}
      {selectedItem && (
        <ItemModal
          item={selectedItem}
          onClose={() => setSelectedItem(null)}
        />
      )}
    </div>
  );
}

/* ─── Sayfalama Bileşeni ─── */

function Pagination({
  current,
  total,
  onChange,
}: {
  current: number;
  total: number;
  onChange: (p: number) => void;
}) {
  const pages = useMemo(() => {
    const result: (number | "...")[] = [];
    if (total <= 7) {
      for (let i = 1; i <= total; i++) result.push(i);
    } else {
      result.push(1);
      if (current > 3) result.push("...");
      const start = Math.max(2, current - 1);
      const end = Math.min(total - 1, current + 1);
      for (let i = start; i <= end; i++) result.push(i);
      if (current < total - 2) result.push("...");
      result.push(total);
    }
    return result;
  }, [current, total]);

  return (
    <nav className="mx-auto mt-12 flex items-center justify-center gap-1">
      <button
        type="button"
        disabled={current === 1}
        onClick={() => onChange(current - 1)}
        className="flex size-9 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-muted disabled:opacity-30"
      >
        <ChevronLeftIcon className="size-4" />
      </button>

      {pages.map((p, i) =>
        p === "..." ? (
          <span
            key={`dots-${i}`}
            className="flex size-9 items-center justify-center text-sm text-muted-foreground"
          >
            ...
          </span>
        ) : (
          <button
            key={p}
            type="button"
            onClick={() => onChange(p)}
            className={`flex size-9 items-center justify-center rounded-lg text-sm font-medium transition-colors ${
              p === current
                ? "bg-primary text-primary-foreground"
                : "text-muted-foreground hover:bg-muted"
            }`}
          >
            {p}
          </button>
        )
      )}

      <button
        type="button"
        disabled={current === total}
        onClick={() => onChange(current + 1)}
        className="flex size-9 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-muted disabled:opacity-30"
      >
        <ChevronRightIcon className="size-4" />
      </button>
    </nav>
  );
}

/* ─── Modal Bileşeni ─── */

function ItemModal({
  item,
  onClose,
}: {
  item: Duyuru;
  onClose: () => void;
}) {
  const overlayRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [onClose]);

  useEffect(() => {
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = "";
    };
  }, []);

  return (
    <div
      ref={overlayRef}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm"
      onClick={(e) => {
        if (e.target === overlayRef.current) onClose();
      }}
    >
      <div className="relative flex max-h-[90vh] w-full max-w-3xl flex-col overflow-hidden rounded-2xl bg-background ring-1 ring-foreground/10">
        {/* Kapat butonu */}
        <button
          type="button"
          onClick={onClose}
          className="absolute top-4 right-4 z-10 flex size-8 items-center justify-center rounded-full bg-black/50 text-white transition-colors hover:bg-black/70"
        >
          <XIcon className="size-4" />
        </button>

        <div className="overflow-y-auto">
          {/* Kapak görseli */}
          {item.resim_url && (
            <div className="relative w-full">
              <img
                src={item.resim_url}
                alt={item.baslik}
                className="aspect-video w-full object-cover"
              />
            </div>
          )}

          <div className="p-6 sm:p-8">
            {/* Tarih + Tür rozeti */}
            <div className="flex items-center gap-3">
              <p className="text-sm text-muted-foreground">{item.tarih}</p>
              <span
                className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
                  item.tur === "duyuru"
                    ? "bg-blue-500/10 text-blue-400"
                    : "bg-emerald-500/10 text-emerald-400"
                }`}
              >
                {item.tur === "duyuru" ? "Duyuru" : "Haber"}
              </span>
            </div>

            {/* Başlık */}
            <h2 className="mt-2 text-xl font-bold text-foreground sm:text-2xl">
              {item.baslik}
            </h2>

            {/* Tam içerik */}
            {item.tam_icerik ? (
              <div
                className="duyuru-icerik prose prose-invert mt-6 max-w-none text-sm text-muted-foreground prose-headings:text-foreground prose-a:text-primary prose-a:underline prose-strong:text-foreground"
                dangerouslySetInnerHTML={{ __html: item.tam_icerik }}
              />
            ) : (
              <p className="mt-6 text-sm text-muted-foreground">{item.ozet}</p>
            )}

            {/* Kaynak linki */}
            {item.kaynak_url && (
              <div className="mt-8 border-t border-border/40 pt-4">
                <a
                  href={item.kaynak_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-primary underline underline-offset-2 hover:text-primary/80"
                >
                  Kaynak: tubitak.gov.tr
                </a>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
