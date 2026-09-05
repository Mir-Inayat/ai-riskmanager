import type { Metadata } from "next";
import "./globals.css";
import { Sidebar } from "@/components/Sidebar";

export const metadata: Metadata = {
  title: "Aegis | Risk Intelligence Dashboard",
  description: "Cost-Aware Payment-Transaction Fraud Triage with expected loss optimization, explainability, and auditability.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-page text-text-primary min-h-screen flex antialiased">
        {/* Fixed Sidebar */}
        <Sidebar />
        
        {/* Main Content Area */}
        <div className="flex-1 ml-[260px] min-h-screen flex flex-col">
          {/* Top Bar */}
          <header className="sticky top-0 z-30 bg-white/80 backdrop-blur-md border-b border-card-border px-8 py-4 flex items-center justify-between">
            <div className="relative">
              <input
                type="text"
                placeholder="Search transactions, alerts..."
                className="w-80 pl-10 pr-4 py-2.5 rounded-button bg-page border border-card-border text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-brand-500/30 focus:border-brand-500 transition-all"
              />
              <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-badge bg-success-light text-success-dark text-xs font-semibold">
                <span className="w-2 h-2 rounded-full bg-success animate-pulse" />
                Defense Mode Active
              </div>
              <div className="w-px h-6 bg-card-border" />
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-brand-500 text-white flex items-center justify-center text-sm font-semibold">
                  A
                </div>
                <div className="text-sm">
                  <p className="font-semibold text-text-primary">Analyst</p>
                  <p className="text-xs text-text-muted">Risk Team</p>
                </div>
              </div>
            </div>
          </header>

          {/* Page Content */}
          <main className="flex-1 p-8">
            {children}
          </main>

          {/* Footer */}
          <footer className="border-t border-card-border bg-white px-8 py-4">
            <div className="flex items-center justify-between text-xs text-text-muted">
              <div className="flex items-center gap-2">
                <span className="font-semibold text-text-secondary">Aegis Risk Engine</span>
                <span>·</span>
                <span>Razorpay AI Buildathon 2026</span>
              </div>
              <div className="flex items-center gap-3">
                <span>IEEE-CIS Dataset</span>
                <span>·</span>
                <span>Chronological Split</span>
                <span>·</span>
                <span>Deterministic Audit</span>
              </div>
            </div>
          </footer>
        </div>
      </body>
    </html>
  );
}
