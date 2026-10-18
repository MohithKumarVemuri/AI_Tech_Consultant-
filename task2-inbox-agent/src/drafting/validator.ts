import { DraftResult, EmailRecord } from "../email/types";

export interface ValidationReport {
  passed: boolean;
  violations: string[];
  forcedNeedsHuman: boolean;
  adjustedDraft: DraftResult;
}

export function validateDraft(draft: DraftResult, email: EmailRecord): ValidationReport {
  const violations: string[] = [];
  const replyLower = draft.reply.toLowerCase();
  let forcedNeedsHuman = false;

  // Rule 1: refund/quote/complaint categories ALWAYS require human approval per spec
  const humanMandatoryCategories = [
    "refund_cancellation",
    "quote",
    "complaint",
    "project_request",
  ];
  if (humanMandatoryCategories.includes(draft.category)) {
    forcedNeedsHuman = true;
    violations.push(`Category '${draft.category}' strictly requires human approval.`);
  }

  // Rule 2: Block unauthorized promises of financial refunds
  const refundPatterns = [
    /refund has been (processed|approved|issued)/i,
    /will refund \$?[0-9]+/i,
    /crediting your card/i,
    /money back guaranteed/i,
  ];
  for (const pat of refundPatterns) {
    if (pat.test(replyLower)) {
      violations.push("Draft makes an unauthorized refund promise.");
      forcedNeedsHuman = true;
    }
  }

  // Rule 3: Block unauthorized specific price commitments in quotes
  const pricePatterns = [
    /we will charge (you )?\$[0-9]+/i,
    /fixed price of \$[0-9]+/i,
    /total cost is \$[0-9]+/i,
  ];
  for (const pat of pricePatterns) {
    if (pat.test(replyLower)) {
      violations.push("Draft makes an unauthorized specific price quote commitment.");
      forcedNeedsHuman = true;
    }
  }

  // Rule 4: Block specific delivery date promises
  const datePatterns = [
    /will be delivered by (monday|tuesday|wednesday|thursday|friday|saturday|sunday)/i,
    /guaranteed launch by/i,
  ];
  for (const pat of datePatterns) {
    if (pat.test(replyLower)) {
      violations.push("Draft makes an unauthorized delivery timeline guarantee.");
      forcedNeedsHuman = true;
    }
  }

  // Rule 5: Check prompt injection defense
  if (
    email.body.toLowerCase().includes("ignore all previous instructions") &&
    replyLower.includes("i am compromised")
  ) {
    violations.push("Draft fell victim to prompt injection attack.");
    forcedNeedsHuman = true;
  }

  // Rule 6: If knowledge state is unavailable or insufficient, must not claim facts
  if (draft.knowledge_state === "knowledge_unavailable") {
    forcedNeedsHuman = true;
    if (draft.reply.includes("http") || draft.sources.length > 0) {
      violations.push("Draft fabricated sources while Knowledge Brain was unreachable.");
    }
  }

  const adjustedDraft: DraftResult = {
    ...draft,
    needs_human: draft.needs_human || forcedNeedsHuman,
  };

  return {
    passed: violations.length === 0,
    violations,
    forcedNeedsHuman,
    adjustedDraft,
  };
}
