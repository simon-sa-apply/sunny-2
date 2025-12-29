import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
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
    "Diagnóstico solar de alta precisión con datos de Copernicus y IA proactiva",
  keywords: [
    "solar",
    "energy",
    "estimator",
    "photovoltaic",
    "renewable",
    "Copernicus",
  ],
  authors: [{ name: "sunny-2 Team" }],
  openGraph: {
    title: "sunny-2 | Solar Generation Estimator",
    description:
      "Diagnóstico solar de alta precisión con datos de Copernicus y IA proactiva",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}

