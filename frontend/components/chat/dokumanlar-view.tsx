"use client";

import { useEffect, useState } from "react";

type Dokuman = {
  filename: string;
  title: string;
  size_bytes: number;
  download_url: string;
  thumbnail_url: string;
};

export function DokumanlarView() {
  const [items, setItems] = useState<Dokuman[] | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetch("/api/dokumanlar", { cache: "no-store" })
      .then((r) => r.json())
      .then((data: Dokuman[]) => {
        if (!cancelled) setItems(Array.isArray(data) ? data : []);
      })
      .catch(() => {
        if (!cancelled) setItems([]);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const isLoading = items === null;
  const isEmpty = items !== null && items.length === 0;

  return (
    <div className="relative z-1 flex-1 overflow-y-auto pt-8 pb-16 sm:pt-10 sm:pb-20">
      <div className="mx-auto max-w-7xl px-6 lg:px-8">
        <div className="mx-auto flex max-w-2xl flex-col items-center">
          <h2 className="text-center font-semibold text-2xl tracking-tight text-foreground md:text-3xl">
            Dokümanlar
          </h2>
          <p className="mt-3 text-center text-muted-foreground/80 text-sm">
            TÜBİTAK dokümanları, yayınları ve kaynakları.
          </p>
        </div>
        {isEmpty ? (
          <p className="mt-12 text-center text-muted-foreground/70 text-sm">
            Henüz doküman yok.
          </p>
        ) : (
          <div className="mx-auto mt-12 grid max-w-2xl auto-rows-fr grid-cols-1 gap-8 lg:mx-0 lg:max-w-none lg:grid-cols-3">
            {isLoading
              ? Array.from({ length: 6 }).map((_, i) => (
                  <div
                    // biome-ignore lint/suspicious/noArrayIndexKey: skeleton
                    key={i}
                    className="relative isolate flex animate-pulse flex-col justify-end overflow-hidden rounded-2xl bg-muted px-8 pt-48 pb-6 sm:pt-32 lg:pt-48"
                  >
                    <div className="absolute inset-0 -z-10 rounded-2xl inset-ring inset-ring-white/10" />
                  </div>
                ))
              : items?.map((post) => (
                  <article
                    key={post.filename}
                    className="relative isolate flex flex-col justify-end overflow-hidden rounded-2xl bg-muted px-8 pt-48 pb-6 sm:pt-32 lg:pt-48"
                  >
                    <img
                      alt={post.title}
                      src={post.thumbnail_url}
                      className="absolute inset-0 -z-10 size-full object-cover"
                    />
                    <div className="absolute inset-0 -z-10 bg-linear-to-t from-black/80 via-black/40" />
                    <div className="absolute inset-0 -z-10 rounded-2xl inset-ring inset-ring-white/10" />

                    <h3 className="text-lg/6 font-semibold text-white">
                      <a
                        href={post.download_url}
                        rel="noopener noreferrer"
                        target="_blank"
                      >
                        <span className="absolute inset-0" />
                        {post.title}
                      </a>
                    </h3>
                  </article>
                ))}
          </div>
        )}
      </div>
    </div>
  );
}
