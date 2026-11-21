/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  eslint: {
    // ESLint is verified in a dedicated CI job with monorepo NODE_PATH resolution
    ignoreDuringBuilds: true,
  },
};

export default nextConfig;
