import type { NextConfig } from "next";
import withBundleAnalyzer from "@next/bundle-analyzer";

const nextConfig: NextConfig = {
  images: {
    formats: ["image/avif", "image/webp"],
    deviceSizes: [640, 750, 828, 1080, 1200],
    imageSizes: [16, 32, 48, 64, 96, 128, 256],
    remotePatterns: [
      { protocol: "https", hostname: "**" },
    ],
  },
  compress: true,
  productionBrowserSourceMaps: false,
  experimental: {
    optimizePackageImports: ["lucide-react", "recharts"],
  },
  turbopack: {},
  // Иначе /api/x/ (со слэшем) → Next 308 → Django APPEND_SLASH 301 → петля редиректов
  skipTrailingSlashRedirect: true,
  // Server-side proxy: the client bundle calls relative "/api/*"
  // (NEXT_PUBLIC_API_URL=/api), so Next must forward those calls to Django.
  // In docker: BACKEND_URL=http://backend:8000; local dev default: localhost:8000.
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${process.env.BACKEND_URL || "http://localhost:8000"}/api/:path*`,
      },
    ];
  },
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          { key: "X-DNS-Prefetch-Control", value: "on" },
          { key: "Strict-Transport-Security", value: "max-age=63072000; includeSubDomains; preload" },
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
        ],
      },
    ];
  },
};

export default withBundleAnalyzer({ enabled: process.env.ANALYZE === "true" })(nextConfig);
