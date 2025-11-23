import type { Metadata } from "next";
import "./globals.css";
import Header from "@/components/Header";

export const metadata: Metadata = {
  title: "WorldSim Markets - AI Monte Carlo Simulations for Prediction Markets",
  description: "Compare Polymarket odds with AI-powered Monte Carlo simulations. Get data-driven insights for prediction market trading decisions.",
  keywords: ["prediction markets", "polymarket", "monte carlo", "simulation", "AI", "trading signals"],
  openGraph: {
    title: "WorldSim Markets",
    description: "AI Monte Carlo simulations for prediction markets",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased bg-gray-50 min-h-screen">
        <Header />
        <main>{children}</main>
      </body>
    </html>
  );
}
