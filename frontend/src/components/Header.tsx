"use client";

import { useRouter } from "next/navigation";

export default function Header() {
  const router = useRouter();

  return (
    <header className="bg-white border-b border-gray-200">
      <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
        <button
          onClick={() => router.push("/")}
          className="text-xl font-bold text-gray-900 hover:text-blue-600 transition-colors"
        >
          WorldSim Markets
        </button>
        <nav className="flex items-center gap-4">
          <button
            onClick={() => router.push("/browse")}
            className="text-sm text-gray-600 hover:text-gray-900"
          >
            Browse Markets
          </button>
        </nav>
      </div>
    </header>
  );
}
