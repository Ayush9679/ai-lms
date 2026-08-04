import type { Metadata } from "next";
import { AuthProvider } from "@/providers/AuthProvider";
import { QueryProvider } from "@/providers/QueryProvider";
import { ScrollProvider } from "@/providers/ScrollProvider";
import { Toaster } from "react-hot-toast";
import "@/app/globals.css";

export const metadata: Metadata = {
  title: "AI-LMS — Enterprise AI Learning Management System",
  description: "AI-powered LMS with study planners, tutoring chat sessions, flashcards, automated grading, and recommendations.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="antialiased">
        <QueryProvider>
          <AuthProvider>
            <ScrollProvider>
              {children}
              <Toaster
                position="top-right"
                toastOptions={{
                  style: {
                    background: "rgba(20, 20, 25, 0.9)",
                    border: "1px solid rgba(255, 255, 255, 0.08)",
                    color: "#fff",
                    backdropFilter: "blur(12px)",
                    borderRadius: "16px",
                  },
                }}
              />
            </ScrollProvider>
          </AuthProvider>
        </QueryProvider>
      </body>
    </html>
  );
}
