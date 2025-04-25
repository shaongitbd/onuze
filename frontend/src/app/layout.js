'use client';

import { Inter } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/lib/auth";
import Navbar from "@/components/Navbar";
import LeftSidebar from "@/components/LeftSidebar";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";

const inter = Inter({ subsets: ["latin"] });

// Metadata can't be exported from Client Components
// Next.js automatically uses defaults or you can use a separate metadata.js file

export default function RootLayout({ children }) {
  // Create a client for React Query
  const [queryClient] = useState(() => new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 60 * 1000, // 1 minute
        refetchOnWindowFocus: false,
      },
    },
  }));

  return (
    <html lang="en">
      <body className={`${inter.className} bg-gray-100`}>
        <QueryClientProvider client={queryClient}>
          <AuthProvider>
            <Navbar />
            <div className="flex max-w-[1670px] mx-auto px-4 sm:px-6 lg:px-8 pt-4">
              <aside className="w-72 hidden lg:block flex-shrink-0 pr-6">
                <LeftSidebar />
              </aside>
              <main className="flex-1 min-w-0">
                {children}
              </main>
            </div>
          </AuthProvider>
        </QueryClientProvider>
      </body>
    </html>
  );
}
