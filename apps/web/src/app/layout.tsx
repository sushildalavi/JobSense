import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import { Toaster } from 'sonner'
import { Providers } from './providers'
import './globals.css'

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
  display: 'swap',
})

export const metadata: Metadata = {
  title: {
    default: 'ApplyFlow — AI Job Search Copilot',
    template: '%s | ApplyFlow',
  },
  description: 'Your AI-powered job search copilot. Discover, apply, and track jobs automatically.',
  keywords: ['job search', 'AI', 'job tracker', 'resume', 'applications'],
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body className={`${inter.variable} font-sans`}>
        <Providers>
          {children}
          <Toaster
            position="bottom-right"
            toastOptions={{
              style: {
                background: '#111118',
                border: '1px solid #1e1e2e',
                color: '#f1f5f9',
              },
            }}
          />
        </Providers>
      </body>
    </html>
  )
}
