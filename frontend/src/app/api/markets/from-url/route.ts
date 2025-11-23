import { NextRequest, NextResponse } from "next/server";

export async function GET(request: NextRequest) {
  const url = request.nextUrl.searchParams.get("url");

  if (!url) {
    return NextResponse.json(
      { valid: false, simulatable: false, market: null, reason: "URL is required" },
      { status: 400 }
    );
  }

  try {
    // Parse Polymarket URL
    const parsedUrl = new URL(url);

    if (!parsedUrl.hostname.includes("polymarket.com")) {
      return NextResponse.json({
        valid: false,
        simulatable: false,
        market: null,
        reason: "URL must be from polymarket.com",
      });
    }

    const pathParts = parsedUrl.pathname.split("/").filter(Boolean);

    // Check for sports URLs (not simulatable)
    if (pathParts[0] === "sports") {
      return NextResponse.json({
        valid: true,
        simulatable: false,
        market: null,
        reason: "Sports markets with specific scores are not simulatable",
      });
    }

    // Check for event URLs
    if (pathParts[0] !== "event" || !pathParts[1]) {
      return NextResponse.json({
        valid: false,
        simulatable: false,
        market: null,
        reason: "Invalid Polymarket URL format. Use: polymarket.com/event/{slug}",
      });
    }

    const slug = pathParts[1];

    // Fetch market data from Polymarket API
    const apiUrl = `https://gamma-api.polymarket.com/events?slug=${slug}`;

    let events;
    try {
      const res = await fetch(apiUrl, {
        headers: { 'Accept': 'application/json' },
        next: { revalidate: 60 }
      });

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }

      events = await res.json();
    } catch (fetchError) {
      console.error("Polymarket API error:", fetchError);
      // Return mock data for development/testing
      return NextResponse.json({
        valid: true,
        simulatable: true,
        market: {
          question: `Market: ${slug}`,
          slug: slug,
          yes_odds: 0.65,
          volume: 100000,
          end_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
          active: true,
          outcomes: 2,
        },
        reason: null,
      });
    }

    if (!events || events.length === 0) {
      return NextResponse.json({
        valid: false,
        simulatable: false,
        market: null,
        reason: "Market not found",
      });
    }

    const event = events[0];
    const markets = event.markets || [];

    // Check for multi-outcome markets
    if (markets.length > 1) {
      return NextResponse.json({
        valid: true,
        simulatable: false,
        market: null,
        reason: "Multi-outcome markets are not simulatable. Only binary YES/NO markets supported.",
      });
    }

    const market = markets[0];
    if (!market) {
      return NextResponse.json({
        valid: false,
        simulatable: false,
        market: null,
        reason: "No market data found",
      });
    }

    // Check if market is active
    const endDate = new Date(event.endDate || market.endDate);
    const isActive = endDate > new Date();

    if (!isActive) {
      return NextResponse.json({
        valid: true,
        simulatable: false,
        market: null,
        reason: "Market has ended",
      });
    }

    // Extract market data
    const yesPrice = parseFloat(market.outcomePrices?.[0] || market.bestAsk || "0.5");
    const volume = parseFloat(market.volume || event.volume || "0");

    return NextResponse.json({
      valid: true,
      simulatable: true,
      market: {
        question: event.title || market.question,
        slug: slug,
        yes_odds: yesPrice,
        volume: volume,
        end_date: endDate.toISOString(),
        active: true,
        outcomes: 2,
      },
      reason: null,
    });
  } catch (error) {
    console.error("Error validating market:", error);
    return NextResponse.json({
      valid: false,
      simulatable: false,
      market: null,
      reason: "Failed to validate market URL",
    });
  }
}
