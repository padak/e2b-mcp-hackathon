import { NextRequest, NextResponse } from "next/server";
import { simulations } from "../route";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;

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
  });
}
