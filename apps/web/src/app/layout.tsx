import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { NextIntlClientProvider } from "next-intl";
import { getLocale, getMessages } from "next-intl/server";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "sunny-2 | Solar Generation Estimator",
  description:
    "High-precision solar diagnostics with Copernicus data and proactive AI",
  keywords: [
    "solar",
    "energy",
    "estimator",
    "photovoltaic",
    "renewable",
    "Copernicus",
  ],
  authors: [{ name: "Apply Digital" }],
  openGraph: {
    title: "sunny-2 | Solar Generation Estimator",
    description:
      "High-precision solar diagnostics with Copernicus data and proactive AI",
    type: "website",
  },
};

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const locale = await getLocale();
  const messages = await getMessages();

  return (
    <html lang={locale}>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <NextIntlClientProvider messages={messages}>
          {children}
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
