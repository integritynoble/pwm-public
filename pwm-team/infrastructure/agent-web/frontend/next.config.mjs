/** @type {import('next').NextConfig} */
const API_URL = process.env.PWM_API_URL || 'http://localhost:8000';

const nextConfig = {
  reactStrictMode: true,
  output: 'standalone',
  env: {
    PWM_API_URL: API_URL,
  },
  async rewrites() {
    // Let client-side /api/* requests (PNG <img src>, direct download links,
    // client fetches) reach the FastAPI backend. Server components already
    // bypass this and call API_URL directly.
    return [
      { source: '/api/:path*', destination: `${API_URL}/api/:path*` },
    ];
  },
};
export default nextConfig;
