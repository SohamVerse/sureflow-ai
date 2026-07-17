import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Sureflow Agentic OS',
  description: 'Local multi-agent company management software powered by Ollama LLMs',
};

import { Toaster } from 'react-hot-toast';

import { AuthProvider } from '@/lib/AuthContext';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet" />
      </head>
      <body>
        <AuthProvider>
          {children}
        </AuthProvider>
        {/* <Toaster position="bottom-right" toastOptions={{
          style: {
            background: 'var(--bg-secondary)',
            color: 'var(--text-primary)',
            border: '1px solid var(--border)',
            fontSize: '14px',
          }
        }} /> */}
      </body>
    </html>
  );
}
