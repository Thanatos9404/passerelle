import type { NextConfig } from "next";

// Static export: `npm run build` writes ./out, which FastAPI serves at "/".
// trailingSlash makes every route a folder with index.html (/workspace/ -> workspace/index.html),
// which Starlette's StaticFiles(html=True) resolves without custom routing.
const nextConfig: NextConfig = {
  output: "export",
  trailingSlash: true,
  images: { unoptimized: true },
  reactStrictMode: true,
  poweredByHeader: false,
  devIndicators: false,
};

export default nextConfig;
