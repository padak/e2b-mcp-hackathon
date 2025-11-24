import { NextRequest, NextResponse } from "next/server";
import { forwardToBackend } from "@/lib/e2b";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;

  try {
    const response = await forwardToBackend(`/simulations/${id}`);

    if (!response.ok) {
      if (response.status === 404) {
        return NextResponse.json({ error: "Simulation not found" }, { status: 404 });
      }
      const errorData = await response.json().catch(() => ({ error: "Backend error" }));
      return NextResponse.json(errorData, { status: response.status });
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Error fetching simulation:", error);
    return NextResponse.json({
      error: error instanceof Error ? error.message : "Failed to fetch simulation"
    }, { status: 500 });
  }
}
