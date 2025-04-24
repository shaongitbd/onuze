import { Inter } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/lib/auth";
import Navbar from "@/components/Navbar";

const inter = Inter({ subsets: ["latin"] });

export const metadata = {
  title: "Reddit Clone",
  description: "A modern Reddit clone frontend built with Next.js",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className={`${inter.className} bg-gray-100`}>
        <AuthProvider>
          <Navbar />
          <main className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        {children}
          </main>
        </AuthProvider>
      </body>
    </html>
  );
}
