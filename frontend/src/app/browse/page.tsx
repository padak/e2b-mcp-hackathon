"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { MarketCardSkeleton } from "@/components/Skeleton";

interface Market {
  slug: string;
  question: string;
  category: string;
  yes_odds: number;
  volume: number;
  end_date: string;
  url: string;
}

const CATEGORIES = [
  { id: "all", label: "All" },
  { id: "politics", label: "Politics" },
  { id: "world", label: "World" },
  { id: "crypto", label: "Crypto" },
  { id: "finance", label: "Finance" },
  { id: "tech", label: "Tech" },
  { id: "culture", label: "Culture" },
];

export default function BrowsePage() {
  const router = useRouter();
  const [markets, setMarkets] = useState<Market[]>([]);
  const [loading, setLoading] = useState(true);
  const [category, setCategory] = useState("all");
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState("volume");
  const [total, setTotal] = useState(0);

  const fetchMarkets = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        category,
        search,
        sort,
        limit: "20",
      });
      const res = await fetch(`/api/markets?${params}`);
      const data = await res.json();
      setMarkets(data.markets || []);
      setTotal(data.total || 0);
    } catch (error) {
      console.error("Failed to fetch markets:", error);
      setMarkets([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [category, search, sort]);

  useEffect(() => {
    fetchMarkets();
  }, [fetchMarkets]);

  useEffect(() => {
    const timeout = setTimeout(() => {
      fetchMarkets();
    }, 300);
    return () => clearTimeout(timeout);
  }, [search, fetchMarkets]);

  const handleSelectMarket = (market: Market) => {
    router.push(`/?url=${encodeURIComponent(market.url)}`);
  };

  return (
    <div className="min-h-screen p-8">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold">Browse Markets</h1>
          <p className="text-gray-600 mt-2">Select a market to run a simulation</p>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          {/* Search */}
          <div className="mb-4">
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search markets..."
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
            />
          </div>

          {/* Categories */}
          <div className="flex flex-wrap gap-2 mb-4">
            {CATEGORIES.map((cat) => (
              <button
                key={cat.id}
                onClick={() => setCategory(cat.id)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  category === cat.id
                    ? "bg-blue-600 text-white"
                    : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                }`}
              >
                {cat.label}
              </button>
            ))}
          </div>

          {/* Sort */}
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-600">Sort by:</span>
            <select
              value={sort}
              onChange={(e) => setSort(e.target.value)}
              className="px-3 py-1 border border-gray-300 rounded text-sm"
            >
              <option value="volume">Volume</option>
              <option value="odds">Odds</option>
              <option value="end_date">End Date</option>
            </select>
          </div>
        </div>

        {/* Results */}
        <div className="space-y-4">
          {loading ? (
            <div className="space-y-4">
              {[...Array(5)].map((_, i) => (
                <MarketCardSkeleton key={i} />
              ))}
            </div>
          ) : markets.length === 0 ? (
            <div className="text-center py-8 text-gray-500">No markets found</div>
          ) : (
            <>
              <p className="text-sm text-gray-500 mb-4">
                Showing {markets.length} of {total} markets
              </p>
              {markets.map((market) => (
                <div
                  key={market.slug}
                  className="bg-white rounded-lg shadow-md p-4 hover:shadow-lg transition-shadow cursor-pointer"
                  onClick={() => handleSelectMarket(market)}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <h3 className="font-medium text-gray-900 mb-2">
                        {market.question}
                      </h3>
                      <div className="flex items-center gap-4 text-sm text-gray-500">
                        <span className="capitalize bg-gray-100 px-2 py-0.5 rounded">
                          {market.category}
                        </span>
                        <span>Vol: ${(market.volume / 1000).toFixed(0)}k</span>
                        <span>
                          Ends: {new Date(market.end_date).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-bold text-blue-600">
                        {Math.round(market.yes_odds * 100)}%
                      </div>
                      <div className="text-xs text-gray-500">YES</div>
                    </div>
                  </div>
                </div>
              ))}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
