/**
 * ThreatPro - RAKSHAK Intelligence Grid Root Layout
 * Futuristic dark-themed SOC mission control interface.
 */
import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'ThreatPro | RAKSHAK Intelligence Grid',
  description: 'National Digital Public Safety Intelligence Grid - Digital Arrest Detection & Counterfeit Forensics',
  icons: {
    icon: '/favicon.ico',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet" />
      </head>
      <body className="min-h-screen bg-cyber-black text-white antialiased">
        {/* Top navigation bar */}
        <header className="glass-nav fixed top-0 left-0 right-0 z-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-14">
              {/* Logo */}
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 rounded-lg bg-cyber-blue/20 border border-cyber-blue/40 flex items-center justify-center">
                  <svg className="w-5 h-5 text-cyber-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <div>
                  <h1 className="text-sm font-bold text-white tracking-tight">
                    ThreatPro
                  </h1>
                  <p className="text-[10px] text-gray-500 tracking-wider uppercase">RAKSHAK Intelligence Grid</p>
                </div>
              </div>

              {/* Navigation */}
              <nav className="hidden md:flex items-center space-x-1">
                <a href="/" className="px-3 py-2 text-xs font-medium text-gray-300 hover:text-white hover:bg-white/5 rounded-lg transition-all">
                  Command Center
                </a>
                <a href="/dashboard" className="px-3 py-2 text-xs font-medium text-gray-300 hover:text-white hover:bg-white/5 rounded-lg transition-all">
                  Dashboard
                </a>
                <a href="/currency" className="px-3 py-2 text-xs font-medium text-gray-300 hover:text-white hover:bg-white/5 rounded-lg transition-all">
                  Currency Sentinel
                </a>
              </nav>

              {/* Status indicator */}
              <div className="flex items-center space-x-3">
                <div className="flex items-center space-x-1.5">
                  <span className="status-dot active"></span>
                  <span className="text-[10px] text-gray-500 tracking-wider">SYSTEM ACTIVE</span>
                </div>
                <div className="flex items-center space-x-2 text-[10px] text-gray-500">
                  <span>Demo v1.0</span>
                  <span className="text-gray-700">|</span>
                  <span>ThreatPro Demo</span>
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Main content */}
        <main className="pt-14 min-h-screen">
          {children}
        </main>
      </body>
    </html>
  );
}