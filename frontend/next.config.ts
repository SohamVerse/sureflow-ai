import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async redirects() {
    return [
      {
        source: '/',
        destination: '/industrial',
        permanent: false,
      },
    ];
  },
};

export default nextConfig;
