import type { NextConfig } from "next";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const nextConfig: NextConfig = {
  images: {
    unoptimized: true,
  },
  async rewrites() {
    return [
      {
        source: "/static/:path*",
        destination: `${API_URL}/static/:path*`,
      },
    ];
  },
};

export default nextConfig;
