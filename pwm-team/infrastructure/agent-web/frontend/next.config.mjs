/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone',
  env: {
    PWM_API_URL: process.env.PWM_API_URL || 'http://localhost:8000',
  },
};
export default nextConfig;
