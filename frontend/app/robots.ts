import type { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      allow: "/",
      disallow: ["/lk/", "/api/", "/admin/"],
    },
    sitemap: "https://xn--d1abbjawic3ap.xn--p1ai/sitemap.xml",
  };
}
