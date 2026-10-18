import { NextRequest, NextResponse } from "next/server";
import { autonomyManager } from "@/autonomy/manager";

export async function GET() {
  const states = autonomyManager.getAllStates();
  return NextResponse.json(states);
}

export async function POST(req: NextRequest) {
  try {
    const { subcategory, enable } = await req.json();
    const result = autonomyManager.toggleHumanAutonomy(subcategory, enable);
    return NextResponse.json(result);
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}
