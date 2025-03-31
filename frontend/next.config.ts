import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*", // Match any API route
        destination: "http://nginx/api/:path*", // Proxy to Nginx
      },
    ];
  },
};

export default nextConfig;