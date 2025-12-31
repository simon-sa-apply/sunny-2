import type { NextConfig } from "next";
import createNextIntlPlugin from "next-intl/plugin";

const withNextIntl = createNextIntlPlugin("./src/i18n/request.ts");

const nextConfig: NextConfig = {
  reactStrictMode: true,
  experimental: {
    // Enable optimizations for Turborepo
    optimizePackageImports: ["recharts", "maplibre-gl"],
  },
  // API proxy for development only
  // In production, Vercel rewrites handle this via vercel.json
  async rewrites() {
    // Only use localhost rewrite in development
    if (process.env.NODE_ENV === "development") {
      return [
        {
          source: "/api/v1/:path*",
          destination: "http://localhost:8000/api/v1/:path*",
        },
      ];
    }
    return [];
  },
};

export default withNextIntl(nextConfig);
