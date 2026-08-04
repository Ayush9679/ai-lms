"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/providers/AuthProvider";
import { Menu, X, Brain, User as UserIcon, LogOut, ChevronDown, GraduationCap } from "lucide-react";

export const Header: React.FC = () => {
  const { user, logout, isAuthenticated } = useAuth();
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [userDropdownOpen, setUserDropdownOpen] = useState(false);

  const navLinks = [
    { name: "About", href: "/about" },
    { name: "Features", href: "/features" },
    { name: "Pricing", href: "/pricing" },
    { name: "Courses", href: "/courses" },
  ];

  const toggleMobileMenu = () => setMobileMenuOpen(!mobileMenuOpen);

  const getDashboardLink = (role: string) => {
    return `/dashboard/${role}`;
  };

  const isActive = (href: string) => pathname === href;

  return (
    <header className="fixed top-0 left-0 w-full z-50 transition-all duration-300">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-4">
        <div className="glass-panel rounded-full px-6 py-3 flex items-center justify-between shadow-lg">
          
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2 text-white font-bold text-lg hover:opacity-95 transition">
            <div className="bg-gradient-to-tr from-purple-600 to-blue-500 p-1.5 rounded-xl flex items-center justify-center">
              <Brain className="w-5 h-5 text-white" />
            </div>
            <span className="bg-gradient-to-r from-white via-white to-purple-400 bg-clip-text text-transparent tracking-wide font-extrabold">
              AI-LMS
            </span>
          </Link>

          {/* Desktop Navigation Links */}
          <nav className="hidden md:flex items-center gap-8">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className={`text-sm font-medium transition hover:text-white ${
                  isActive(link.href) ? "text-purple-400 font-semibold" : "text-zinc-400"
                }`}
              >
                {link.name}
              </Link>
            ))}
          </nav>

          {/* Authentication Actions */}
          <div className="hidden md:flex items-center gap-4">
            {isAuthenticated && user ? (
              <div className="relative">
                <button
                  onClick={() => setUserDropdownOpen(!userDropdownOpen)}
                  className="flex items-center gap-2 text-zinc-300 hover:text-white transition py-1.5 px-3 rounded-full hover:bg-zinc-800/40 border border-transparent hover:border-zinc-700/50"
                >
                  {user.profile_image ? (
                    <img
                      src={user.profile_image}
                      alt={user.full_name}
                      className="w-6 h-6 rounded-full object-cover"
                    />
                  ) : (
                    <div className="w-6 h-6 rounded-full bg-purple-600 flex items-center justify-center text-xs font-bold text-white">
                      {user.full_name[0].toUpperCase()}
                    </div>
                  )}
                  <span className="text-sm font-medium">{user.full_name.split(" ")[0]}</span>
                  <ChevronDown className={`w-3.5 h-3.5 transition-transform ${userDropdownOpen ? "rotate-180" : ""}`} />
                </button>

                {/* Dropdown Menu */}
                {userDropdownOpen && (
                  <>
                    <div
                      className="fixed inset-0 z-40"
                      onClick={() => setUserDropdownOpen(false)}
                    />
                    <div className="absolute right-0 mt-2 w-52 glass-card rounded-2xl p-2 z-50 flex flex-col gap-1">
                      <div className="px-3 py-2 border-b border-zinc-800/60 mb-1">
                        <p className="text-xs text-zinc-500 font-semibold uppercase tracking-wider">Signed in as</p>
                        <p className="text-sm font-medium text-white truncate">{user.email}</p>
                      </div>
                      <Link
                        href={getDashboardLink(user.role)}
                        onClick={() => setUserDropdownOpen(false)}
                        className="flex items-center gap-2.5 px-3 py-2 text-sm text-zinc-300 hover:text-white rounded-xl hover:bg-zinc-800/60 transition"
                      >
                        <GraduationCap className="w-4 h-4 text-purple-400" />
                        Dashboard
                      </Link>
                      <button
                        onClick={() => {
                          setUserDropdownOpen(false);
                          logout();
                        }}
                        className="flex items-center gap-2.5 px-3 py-2 text-sm text-red-400 hover:text-red-300 rounded-xl hover:bg-red-950/20 transition text-left"
                      >
                        <LogOut className="w-4 h-4" />
                        Log out
                      </button>
                    </div>
                  </>
                )}
              </div>
            ) : (
              <>
                <Link
                  href="/login"
                  className="text-sm text-zinc-400 hover:text-white transition font-medium px-4 py-2"
                >
                  Log in
                </Link>
                <Link
                  href="/register"
                  className="glow-btn text-sm bg-gradient-to-r from-purple-600 to-blue-500 hover:from-purple-500 hover:to-blue-400 text-white font-semibold px-5 py-2.5 rounded-full shadow-lg hover:shadow-purple-500/20 transition-all border border-purple-500/30"
                >
                  Get Started
                </Link>
              </>
            )}
          </div>

          {/* Mobile menu toggle */}
          <div className="flex md:hidden items-center">
            <button
              onClick={toggleMobileMenu}
              className="text-zinc-400 hover:text-white focus:outline-none p-1.5 rounded-full hover:bg-zinc-900/50"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Drawer Menu */}
      {mobileMenuOpen && (
        <>
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 md:hidden" onClick={toggleMobileMenu} />
          <div className="fixed top-24 left-4 right-4 z-50 glass-card rounded-3xl p-6 md:hidden flex flex-col gap-4 animate-in fade-in slide-in-from-top-5 duration-200">
            <nav className="flex flex-col gap-4">
              {navLinks.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  onClick={toggleMobileMenu}
                  className={`text-base font-semibold hover:text-white transition ${
                    isActive(link.href) ? "text-purple-400" : "text-zinc-400"
                  }`}
                >
                  {link.name}
                </Link>
              ))}
            </nav>

            <div className="h-px bg-zinc-800/80 my-2" />

            <div className="flex flex-col gap-3">
              {isAuthenticated && user ? (
                <>
                  <div className="flex items-center gap-3 px-1 py-1">
                    {user.profile_image ? (
                      <img
                        src={user.profile_image}
                        alt={user.full_name}
                        className="w-10 h-10 rounded-full object-cover"
                      />
                    ) : (
                      <div className="w-10 h-10 rounded-full bg-purple-600 flex items-center justify-center font-bold text-white text-base">
                        {user.full_name[0].toUpperCase()}
                      </div>
                    )}
                    <div>
                      <p className="text-sm font-semibold text-white">{user.full_name}</p>
                      <p className="text-xs text-zinc-500">{user.email}</p>
                    </div>
                  </div>
                  <Link
                    href={getDashboardLink(user.role)}
                    onClick={toggleMobileMenu}
                    className="w-full flex items-center justify-center gap-2 bg-zinc-800/80 text-white font-semibold py-3 rounded-2xl border border-zinc-700/60 transition"
                  >
                    Dashboard
                  </Link>
                  <button
                    onClick={() => {
                      toggleMobileMenu();
                      logout();
                    }}
                    className="w-full flex items-center justify-center gap-2 bg-red-950/20 text-red-400 font-semibold py-3 rounded-2xl border border-red-900/30 transition"
                  >
                    Log out
                  </button>
                </>
              ) : (
                <>
                  <Link
                    href="/login"
                    onClick={toggleMobileMenu}
                    className="w-full text-center text-zinc-300 hover:text-white font-semibold py-3 rounded-2xl hover:bg-zinc-900 transition"
                  >
                    Log in
                  </Link>
                  <Link
                    href="/register"
                    onClick={toggleMobileMenu}
                    className="w-full text-center bg-gradient-to-r from-purple-600 to-blue-500 text-white font-semibold py-3 rounded-2xl transition"
                  >
                    Get Started
                  </Link>
                </>
              )}
            </div>
          </div>
        </>
      )}
    </header>
  );
};
export default Header;
