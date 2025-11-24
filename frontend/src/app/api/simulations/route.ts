import { NextRequest, NextResponse } from "next/server";
import { forwardToBackend } from "@/lib/e2b";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { market_url, n_runs = 200, question, yes_odds } = body;

    if (!market_url) {
      return NextResponse.json({ error: "market_url is required" }, { status: 400 });
    }

    // Forward to E2B backend
    const response = await forwardToBackend("/simulations", {
      method: "POST",
      body: JSON.stringify({
        market_url,
        question: question || "Unknown market",
        yes_odds: yes_odds || 0.5,
        n_runs,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: "Backend error" }));
      return NextResponse.json(errorData, { status: response.status });
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Error creating simulation:", error);
    return NextResponse.json({
      error: error instanceof Error ? error.message : "Failed to create simulation"
    }, { status: 500 });
  }
}
