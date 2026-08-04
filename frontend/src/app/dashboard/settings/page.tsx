"use client";

import React, { useState } from "react";
import { DashboardLayout } from "@/components/dashboard/DashboardLayout";
import { PageTransition } from "@/components/shared/PageTransitions";
import { Bell, Shield, Zap } from "lucide-react";
import toast from "react-hot-toast";

export default function SettingsPage() {
  const [emailAlerts, setEmailAlerts] = useState(true);
  const [aiSuggestions, setAiSuggestions] = useState(true);
  const [doubleFactor, setDoubleFactor] = useState(false);

  const handleSave = () => {
    toast.success("Settings saved successfully!");
  };

  return (
    <DashboardLayout>
      <PageTransition>
        <div className="max-w-3xl mx-auto flex flex-col gap-8 text-left">
          <div>
            <h1 className="text-3xl font-extrabold text-white">System Settings</h1>
            <p className="text-zinc-400 text-sm mt-1">Configure account alerts, privacy parameters, and AI tutor presets.</p>
          </div>

          <div className="flex flex-col gap-6">
            {/* Row 1 */}
            <div className="glass-card rounded-3xl p-6 flex items-start gap-4">
              <div className="p-3 bg-purple-950/40 rounded-2xl flex items-center justify-center">
                <Bell className="w-5 h-5 text-purple-400" />
              </div>
              <div className="flex-1">
                <h3 className="text-base font-bold text-white">Notifications</h3>
                <p className="text-xs text-zinc-500 mt-1 leading-relaxed">Receive updates about graded assignments and exam dates via email.</p>
                <div className="flex items-center gap-3 mt-4">
                  <input
                    type="checkbox"
                    checked={emailAlerts}
                    onChange={(e) => setEmailAlerts(e.target.checked)}
                    className="w-4 h-4 rounded text-purple-600 bg-zinc-950 border-zinc-800 focus:ring-purple-500"
                  />
                  <span className="text-sm font-semibold text-zinc-300">Enable Email Notifications</span>
                </div>
              </div>
            </div>

            {/* Row 2 */}
            <div className="glass-card rounded-3xl p-6 flex items-start gap-4">
              <div className="p-3 bg-blue-950/40 rounded-2xl flex items-center justify-center">
                <Zap className="w-5 h-5 text-blue-400" />
              </div>
              <div className="flex-1">
                <h3 className="text-base font-bold text-white">AI Copilot</h3>
                <p className="text-xs text-zinc-500 mt-1 leading-relaxed">Let Gemini AI automatically propose weaknesses study paths inside notes.</p>
                <div className="flex items-center gap-3 mt-4">
                  <input
                    type="checkbox"
                    checked={aiSuggestions}
                    onChange={(e) => setAiSuggestions(e.target.checked)}
                    className="w-4 h-4 rounded text-purple-600 bg-zinc-950 border-zinc-800 focus:ring-purple-500"
                  />
                  <span className="text-sm font-semibold text-zinc-300">Enable AI Weakness Recommendations</span>
                </div>
              </div>
            </div>

            {/* Row 3 */}
            <div className="glass-card rounded-3xl p-6 flex items-start gap-4">
              <div className="p-3 bg-pink-950/40 rounded-2xl flex items-center justify-center">
                <Shield className="w-5 h-5 text-pink-400" />
              </div>
              <div className="flex-1">
                <h3 className="text-base font-bold text-white">Security & Privacy</h3>
                <p className="text-xs text-zinc-500 mt-1 leading-relaxed">Require two-factor authentication tokens during logins.</p>
                <div className="flex items-center gap-3 mt-4">
                  <input
                    type="checkbox"
                    checked={doubleFactor}
                    onChange={(e) => setDoubleFactor(e.target.checked)}
                    className="w-4 h-4 rounded text-purple-600 bg-zinc-950 border-zinc-800 focus:ring-purple-500"
                  />
                  <span className="text-sm font-semibold text-zinc-300">Enable 2FA (Two Factor Authentication)</span>
                </div>
              </div>
            </div>

            <button
              onClick={handleSave}
              className="glow-btn py-3.5 px-6 text-sm font-bold bg-gradient-to-r from-purple-600 to-blue-500 text-white rounded-xl shadow-lg transition w-fit cursor-pointer"
            >
              Save Configuration
            </button>
          </div>
        </div>
      </PageTransition>
    </DashboardLayout>
  );
}
