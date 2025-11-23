import { NextRequest, NextResponse } from "next/server";
import { forwardToBackend } from "@/lib/e2b";

// Check if we should use E2B backend or mock
const USE_E2B = process.env.E2B_API_KEY && process.env.NODE_ENV === "production";

// Mock market data for different categories
const MOCK_MARKETS = [
  // Politics
  { slug: "presidential-2024", question: "Will the incumbent party win the 2024 election?", category: "politics", yes_odds: 0.45, volume: 2500000, end_date: "2024-11-05" },
  { slug: "senate-control-2024", question: "Will Democrats control the Senate after 2024?", category: "politics", yes_odds: 0.52, volume: 800000, end_date: "2024-11-05" },
  { slug: "impeachment-2024", question: "Will there be a presidential impeachment in 2024?", category: "politics", yes_odds: 0.08, volume: 150000, end_date: "2024-12-31" },

  // World
  { slug: "ukraine-ceasefire", question: "Will there be a Ukraine ceasefire by end of 2024?", category: "world", yes_odds: 0.22, volume: 450000, end_date: "2024-12-31" },
  { slug: "china-taiwan-2024", question: "Will China take military action against Taiwan in 2024?", category: "world", yes_odds: 0.05, volume: 320000, end_date: "2024-12-31" },
  { slug: "un-reform-2024", question: "Will the UN Security Council be reformed in 2024?", category: "world", yes_odds: 0.12, volume: 85000, end_date: "2024-12-31" },

  // Crypto
  { slug: "btc-100k-2024", question: "Will Bitcoin reach $100k in 2024?", category: "crypto", yes_odds: 0.65, volume: 1800000, end_date: "2024-12-31" },
  { slug: "eth-merge-issues", question: "Will Ethereum face major issues in 2024?", category: "crypto", yes_odds: 0.18, volume: 220000, end_date: "2024-12-31" },
  { slug: "crypto-regulation-us", question: "Will the US pass major crypto regulation in 2024?", category: "crypto", yes_odds: 0.35, volume: 380000, end_date: "2024-12-31" },

  // Finance
  { slug: "fed-rate-cut-dec", question: "Will the Fed cut rates in December 2024?", category: "finance", yes_odds: 0.72, volume: 950000, end_date: "2024-12-18" },
  { slug: "recession-2024", question: "Will the US enter recession in 2024?", category: "finance", yes_odds: 0.28, volume: 620000, end_date: "2024-12-31" },
  { slug: "sp500-ath-2024", question: "Will S&P 500 hit new all-time high in 2024?", category: "finance", yes_odds: 0.78, volume: 540000, end_date: "2024-12-31" },

  // Tech
  { slug: "agi-2024", question: "Will AGI be achieved in 2024?", category: "tech", yes_odds: 0.02, volume: 180000, end_date: "2024-12-31" },
  { slug: "apple-ai-device", question: "Will Apple release a standalone AI device in 2024?", category: "tech", yes_odds: 0.25, volume: 290000, end_date: "2024-12-31" },
  { slug: "twitter-profitability", question: "Will X/Twitter become profitable in 2024?", category: "tech", yes_odds: 0.32, volume: 195000, end_date: "2024-12-31" },

  // Culture
  { slug: "taylor-swift-tour", question: "Will Taylor Swift announce another world tour in 2024?", category: "culture", yes_odds: 0.45, volume: 120000, end_date: "2024-12-31" },
  { slug: "oscars-streaming", question: "Will a streaming film win Best Picture at 2024 Oscars?", category: "culture", yes_odds: 0.55, volume: 85000, end_date: "2024-03-10" },
];

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const category = searchParams.get("category");
  const search = searchParams.get("search");
  const sort = searchParams.get("sort") || "volume";
  const limit = parseInt(searchParams.get("limit") || "10");
  const offset = parseInt(searchParams.get("offset") || "0");

  // Use E2B backend in production for real Polymarket data
  if (USE_E2B) {
    try {
      const params = new URLSearchParams({
        ...(category && { category }),
        ...(search && { search_query: search }),
        limit: limit.toString(),
      });
      const response = await forwardToBackend(`/markets?${params}`);
      const data = await response.json();
      return NextResponse.json(data);
    } catch (error) {
      console.error("E2B backend error:", error);
      // Fall through to mock data
    }
  }

  // Mock implementation
  let markets = [...MOCK_MARKETS];

  // Filter by category
  if (category && category !== "all") {
    markets = markets.filter(m => m.category === category);
  }

  // Filter by search
  if (search) {
    const searchLower = search.toLowerCase();
    markets = markets.filter(m =>
      m.question.toLowerCase().includes(searchLower) ||
      m.slug.toLowerCase().includes(searchLower)
    );
  }

  // Sort
  if (sort === "volume") {
    markets.sort((a, b) => b.volume - a.volume);
  } else if (sort === "odds") {
    markets.sort((a, b) => b.yes_odds - a.yes_odds);
  } else if (sort === "end_date") {
    markets.sort((a, b) => new Date(a.end_date).getTime() - new Date(b.end_date).getTime());
  }

  // Pagination
  const total = markets.length;
  markets = markets.slice(offset, offset + limit);

  return NextResponse.json({
    markets: markets.map(m => ({
      ...m,
      url: `https://polymarket.com/event/${m.slug}`,
    })),
    total,
    offset,
    limit,
  });
}
