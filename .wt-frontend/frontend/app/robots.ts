import type { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      allow: "/",
      disallow: ["/lk/", "/api/", "/admin/"],
    },
    sitemap: "https://минитендер.рф/sitemap.xml",
  };
}
