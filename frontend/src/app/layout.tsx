import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'AgentMind',
  description: 'Платформа для управління пам\'яттю самонавчальних ШІ-агентів',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="uk">
      <body>{children}</body>
    </html>
  )
}

