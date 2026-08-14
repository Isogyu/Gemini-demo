/** @type {import('next').NextConfig} */
const nextConfig = {
  output: process.env.NEXT_OUTPUT ?? "standalone",
  reactStrictMode: true,
};

export default nextConfig;
