import { NextRequest, NextResponse } from "next/server";
import { forwardToBackend } from "@/lib/e2b";
import { simulations } from "../route";

// Check if we should use E2B backend or mock
const USE_E2B = process.env.E2B_API_KEY && process.env.NODE_ENV === "production";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;

  // Use E2B backend in production
  if (USE_E2B) {
    try {
      const response = await forwardToBackend(`/simulations/${id}`);
      const data = await response.json();
      return NextResponse.json(data);
    } catch (error) {
      console.error("E2B backend error:", error);
      return NextResponse.json({ error: "Backend unavailable" }, { status: 503 });
    }
  }

  // Mock implementation for development
  const simulation = simulations.get(id);

  if (!simulation) {
    return NextResponse.json({ error: "Simulation not found" }, { status: 404 });
  }

  return NextResponse.json({
    id: simulation.id,
    status: simulation.status,
    progress: simulation.progress,
    result: simulation.result,
    error: simulation.error,
    logs: simulation.logs,
  });
}
