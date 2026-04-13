import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import localFont from "next/font/local";
import { TooltipProvider } from "@/components/ui/tooltip";

import "./globals.css";
import { SessionProvider } from "next-auth/react";

export const metadata: Metadata = {
  metadataBase: new URL("http://localhost:3000"),
  title: "Tubibot",
  description: "TÜBİTAK 2209-A Asistanı",
};

export const viewport = {
  maximumScale: 1,
};

const geist = Geist({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-geist",
});

const geistMono = Geist_Mono({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-geist-mono",
});

const monaSans = localFont({
  src: "../public/fonts/Mona-Sans.var.woff2",
  display: "swap",
  variable: "--font-mona-sans",
  weight: "200 900",
});

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      className={`${geist.variable} ${geistMono.variable} ${monaSans.variable} dark`}
      lang="tr"
      suppressHydrationWarning
    >
      <head>
        <meta name="theme-color" content="hsl(240deg 10% 3.92%)" />
      </head>
      <body className="antialiased">
        <SessionProvider
          basePath={`${process.env.NEXT_PUBLIC_BASE_PATH ?? ""}/api/auth`}
        >
          <TooltipProvider>{children}</TooltipProvider>
        </SessionProvider>
      </body>
    </html>
  );
}
