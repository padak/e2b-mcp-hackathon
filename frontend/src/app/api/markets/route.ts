import { NextRequest, NextResponse } from "next/server";

const GAMMA_API_URL = "https://gamma-api.polymarket.com";

interface PolymarketMarket {
  id?: string;
  slug?: string;
  groupSlug?: string;
  question?: string;
  outcomePrices?: string | number[];
  volumeNum?: number;
  volume?: number;
  endDate?: string;
  closed?: boolean;
  oneDayPriceChange?: number;
}

function formatMarket(m: PolymarketMarket) {
  // Parse outcome prices
  let outcomePrices = m.outcomePrices;
  if (typeof outcomePrices === "string") {
    try {
      outcomePrices = JSON.parse(outcomePrices);
    } catch {
      outcomePrices = [];
    }
  }

  const yesOdds = Array.isArray(outcomePrices) && outcomePrices.length > 0
    ? parseFloat(String(outcomePrices[0]))
    : 0.5;

  const volume = m.volumeNum || m.volume || 0;

  // Build correct URL: /event/{eventSlug}/{marketSlug}
  const marketSlug = m.slug || m.id || "";
  const eventSlug = m.groupSlug || marketSlug;
  const url = eventSlug !== marketSlug
    ? `https://polymarket.com/event/${eventSlug}/${marketSlug}`
    : `https://polymarket.com/event/${marketSlug}`;

  return {
    slug: marketSlug,
    question: m.question || "Unknown",
    yes_odds: yesOdds,
    volume: typeof volume === "number" ? volume : parseFloat(String(volume)) || 0,
    end_date: m.endDate || "",
    url,
  };
}

async function getMarkets(limit: number = 50): Promise<PolymarketMarket[]> {
  const params = new URLSearchParams({
    limit: String(limit * 3),
    active: "true",
    closed: "false",
  });

  const response = await fetch(`${GAMMA_API_URL}/markets?${params}`);
  if (!response.ok) return [];

  const markets = await response.json();
  if (!Array.isArray(markets)) return [];

  // Sort by volume descending
  markets.sort((a: PolymarketMarket, b: PolymarketMarket) => {
    const volA = a.volumeNum || a.volume || 0;
    const volB = b.volumeNum || b.volume || 0;
    return (typeof volB === "number" ? volB : 0) - (typeof volA === "number" ? volA : 0);
  });

  return markets.slice(0, limit);
}

async function getBiggestMovers(category: string, limit: number = 10): Promise<PolymarketMarket[]> {
  const response = await fetch(
    `https://polymarket.com/api/biggest-movers?category=${category}`
  );
  if (!response.ok) return [];

  const data = await response.json();
  return (data.markets || []).slice(0, limit);
}

async function searchMarkets(query: string, limit: number = 10): Promise<PolymarketMarket[]> {
  const params = new URLSearchParams({
    q: query,
    limit_per_type: "50",
  });

  const response = await fetch(`${GAMMA_API_URL}/public-search?${params}`);
  if (!response.ok) return [];

  const data = await response.json();

  // Extract active markets from events
  const markets: PolymarketMarket[] = [];
  for (const event of data.events || []) {
    for (const market of event.markets || []) {
      if (!market.closed) {
        markets.push(market);
      }
    }
  }

  // Dedupe and sort by volume
  const seen = new Set<string>();
  const unique: PolymarketMarket[] = [];
  for (const m of markets) {
    const mid = m.id || m.slug;
    if (mid && !seen.has(mid)) {
      seen.add(mid);
      unique.push(m);
    }
  }

  unique.sort((a, b) => {
    const volA = a.volumeNum || a.volume || 0;
    const volB = b.volumeNum || b.volume || 0;
    return (typeof volB === "number" ? volB : 0) - (typeof volA === "number" ? volA : 0);
  });

  return unique.slice(0, limit);
}

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const category = searchParams.get("category");
  const search = searchParams.get("search");
  const limit = parseInt(searchParams.get("limit") || "20");

  try {
    let rawMarkets: PolymarketMarket[] = [];

    if (search) {
      // Search query takes priority
      rawMarkets = await searchMarkets(search, limit);
    } else if (category && category !== "all") {
      // Get biggest movers for category
      rawMarkets = await getBiggestMovers(category, limit);
    } else {
      // Get top markets by volume
      rawMarkets = await getMarkets(limit);
    }

    const markets = rawMarkets.map(formatMarket);

    return NextResponse.json({
      markets,
      total: markets.length,
      offset: 0,
      limit,
    });
  } catch (error) {
    console.error("Error fetching markets:", error);
    return NextResponse.json(
      { error: "Failed to fetch markets" },
      { status: 500 }
    );
  }
}
