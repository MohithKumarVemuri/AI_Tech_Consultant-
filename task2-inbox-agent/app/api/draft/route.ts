import { NextRequest, NextResponse } from "next/server";
import { classifyEmail } from "@/drafting/classifier";
import { generateDraft } from "@/drafting/drafter";
import { EmailRecord } from "@/email/types";

export async function POST(req: NextRequest) {
  try {
    const email: EmailRecord = await req.json();
    const classification = await classifyEmail(email);
    const { draft, validation } = await generateDraft(email, classification);

    return NextResponse.json({
      classification,
      draft,
      validation,
    });
  } catch (error: any) {
    return NextResponse.json({ error: error.message || "Drafting failed" }, { status: 500 });
  }
}
