/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Для роботи в Docker
  output: 'standalone',
  // WebSocket підтримка
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: process.env.NEXT_PUBLIC_BACKEND_URL + '/api/:path*',
      },
    ]
  },
}

module.exports = nextConfig

