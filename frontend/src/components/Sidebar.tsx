"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  ShieldAlert,
  FileSearch,
  Settings2,
  Activity,
  HelpCircle,
  Shield,
} from "lucide-react";

const menuItems = [
  { label: "Dashboard", href: "/", icon: LayoutDashboard },
  { label: "Alert Queue", href: "/alerts", icon: ShieldAlert },
  { label: "Policy & Health", href: "/policy", icon: Settings2 },
];

const secondaryItems = [
  { label: "Model Status", href: "/policy", icon: Activity },
  { label: "Help Center", href: "#", icon: HelpCircle },
];

export const Sidebar: React.FC = () => {
  const pathname = usePathname();

  const isActive = (href: string) => {
    if (href === "/") return pathname === "/";
    return pathname.startsWith(href);
  };

  return (
    <aside className="fixed left-0 top-0 bottom-0 w-[260px] bg-sidebar flex flex-col z-40 shadow-sidebar">
      {/* Logo */}
      <div className="px-6 py-6 flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-brand-500 flex items-center justify-center">
          <Shield className="w-5 h-5 text-white" />
        </div>
        <div>
          <h1 className="text-white text-lg font-bold tracking-tight">Aegis</h1>
          <p className="text-slate-400 text-[11px]">Risk Intelligence</p>
        </div>
      </div>

      {/* Divider */}
      <div className="mx-5 h-px bg-white/10" />

      {/* Main Menu */}
      <nav className="flex-1 px-4 py-6">
        <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider px-3 mb-3">
          Menu
        </p>
        <ul className="space-y-1">
          {menuItems.map((item) => {
            const active = isActive(item.href);
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${
                    active
                      ? "bg-brand-500 text-white shadow-md shadow-brand-500/30"
                      : "text-slate-400 hover:text-white hover:bg-sidebar-hover"
                  }`}
                >
                  <item.icon className="w-[18px] h-[18px]" />
                  <span>{item.label}</span>
                </Link>
              </li>
            );
          })}
        </ul>

        {/* Secondary */}
        <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider px-3 mb-3 mt-8">
          General
        </p>
        <ul className="space-y-1">
          {secondaryItems.map((item) => (
            <li key={item.label}>
              <Link
                href={item.href}
                className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-slate-400 hover:text-white hover:bg-sidebar-hover transition-all duration-200"
              >
                <item.icon className="w-[18px] h-[18px]" />
                <span>{item.label}</span>
              </Link>
            </li>
          ))}
        </ul>
      </nav>

      {/* Bottom Card */}
      <div className="px-4 pb-6">
        <div className="rounded-xl bg-gradient-to-br from-brand-600 to-brand-700 p-4 text-white">
          <div className="flex items-center gap-2 mb-2">
            <Activity className="w-4 h-4" />
            <span className="text-xs font-semibold">Pipeline Health</span>
          </div>
          <p className="text-[11px] text-white/70 leading-relaxed">
            4-layer defense active. ~11ms avg latency. All systems nominal.
          </p>
          <Link
            href="/policy"
            className="mt-3 block text-center text-xs font-semibold bg-white/20 hover:bg-white/30 rounded-lg py-2 transition-colors"
          >
            View Details
          </Link>
        </div>
      </div>
    </aside>
  );
};
