import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Core layout
        sidebar: "#1A1D2E",
        "sidebar-hover": "#252840",
        "sidebar-active": "#2D3152",
        page: "#F3F4F8",
        
        // Card & surface
        card: "#FFFFFF",
        "card-border": "#E8EAF0",
        
        // Brand accent (indigo-violet for trust/security)
        brand: {
          50: "#EEF2FF",
          100: "#E0E7FF",
          400: "#818CF8",
          500: "#6366F1",
          600: "#4F46E5",
          700: "#4338CA",
        },
        
        // Semantic
        success: { light: "#ECFDF5", DEFAULT: "#10B981", dark: "#059669" },
        warning: { light: "#FFFBEB", DEFAULT: "#F59E0B", dark: "#D97706" },
        danger:  { light: "#FEF2F2", DEFAULT: "#EF4444", dark: "#DC2626" },
        info:    { light: "#EFF6FF", DEFAULT: "#3B82F6", dark: "#2563EB" },
        
        // Text
        "text-primary": "#1E293B",
        "text-secondary": "#64748B",
        "text-muted": "#94A3B8",
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "-apple-system", "sans-serif"],
      },
      borderRadius: {
        'card': '16px',
        'badge': '8px',
        'button': '10px',
      },
      boxShadow: {
        'card': '0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.06)',
        'card-hover': '0 4px 12px rgba(0,0,0,0.08)',
        'sidebar': '4px 0 24px rgba(0,0,0,0.12)',
      },
    },
  },
  plugins: [],
};
export default config;
