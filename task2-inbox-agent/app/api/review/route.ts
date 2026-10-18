import { NextRequest, NextResponse } from "next/server";
import { calculateEditDiff } from "@/feedback/edit-diff";
import { saveFeedback } from "@/feedback/feedback-store";
import { autonomyManager } from "@/autonomy/manager";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const {
      emailId,
      category,
      subcategory,
      originalDraft,
      finalReply,
      action,
      editReason,
      reviewer = "Human Operator",
      promptVersion = "drafting@v1",
      model = "claude-haiku-5-5",
    } = body;

    // 1. Calculate diff
    const diff = calculateEditDiff(originalDraft || "", finalReply || "");

    // 2. Save feedback record
    saveFeedback({
      id: `fb_${Date.now()}`,
      emailId,
      category,
      subcategory,
      originalDraft: originalDraft || "",
      finalReply: finalReply || "",
      action,
      editReason,
      similarity: diff.similarity,
      isUnchanged: diff.isUnchanged,
      reviewer,
      promptVersion,
      model,
      timestamp: new Date().toISOString(),
    });

    // 3. Update autonomy state machine
    const updatedState = autonomyManager.recordOutcome(subcategory, action, diff.isUnchanged);

    return NextResponse.json({
      success: true,
      diff,
      autonomy: updatedState,
      message: `Action '${action}' recorded successfully. Simulated email dispatch completed.`,
    });
  } catch (error: any) {
    return NextResponse.json({ error: error.message || "Review recording failed" }, { status: 500 });
  }
}
