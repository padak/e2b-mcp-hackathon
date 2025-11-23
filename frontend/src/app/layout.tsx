import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "WorldSim Markets",
  description: "AI world simulator comparing Polymarket odds with Monte Carlo simulations",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased bg-gray-50">
        {children}
      </body>
    </html>
  );
}
