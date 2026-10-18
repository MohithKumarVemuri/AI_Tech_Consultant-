import { NextRequest, NextResponse } from "next/server";
import {
  runNightlyPromptOptimizer,
  getPromptProposals,
  updateProposalStatus,
} from "@/feedback/nightly-optimizer";

export async function GET() {
  const proposals = getPromptProposals();
  return NextResponse.json(proposals);
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    if (body.action === "run_optimization") {
      const proposals = runNightlyPromptOptimizer();
      return NextResponse.json({ success: true, proposals });
    }
    if (body.action === "update_status") {
      const { version, status } = body;
      const ok = updateProposalStatus(version, status);
      return NextResponse.json({ success: ok });
    }
    return NextResponse.json({ error: "Unknown action" }, { status: 400 });
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}
