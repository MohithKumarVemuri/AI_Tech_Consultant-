import { describe, it, expect } from "vitest";
import { validateDraft } from "../src/drafting/validator";
import { DraftResult, EmailRecord } from "../src/email/types";

describe("Draft Validator", () => {
  const dummyEmail: EmailRecord = {
    id: "em_test",
    subject: "Refund request",
    sender: "user@test.com",
    received_at: new Date().toISOString(),
    body: "Please refund my $99",
    expected_category: "refund_cancellation",
    subcategory: "refund_cancellation/request",
    risk: "high",
    key_facts: ["Refund request"],
    expected_behavior: "Block auto promise",
    is_test_holdout: false,
  };

  it("blocks unauthorized financial refund promises", () => {
    const dangerousDraft: DraftResult = {
      category: "refund_cancellation",
      summary: "Processed refund",
      reply: "Your refund has been processed back to your credit card.",
      sources: [],
      risk: "high",
      needs_human: false,
      next_action: "send",
      prompt_version: "v1",
      knowledge_state: "grounded",
    };

    const result = validateDraft(dangerousDraft, dummyEmail);
    expect(result.passed).toBe(false);
    expect(result.forcedNeedsHuman).toBe(true);
    expect(result.violations.some((v) => v.includes("refund promise"))).toBe(true);
  });

  it("enforces human review for quote categories", () => {
    const quoteDraft: DraftResult = {
      category: "quote",
      summary: "Quote details",
      reply: "We charge $5,000 for WordPress migration.",
      sources: [],
      risk: "medium",
      needs_human: false,
      next_action: "send",
      prompt_version: "v1",
      knowledge_state: "grounded",
    };

    const result = validateDraft(quoteDraft, dummyEmail);
    expect(result.forcedNeedsHuman).toBe(true);
    expect(result.violations.some((v) => v.includes("price quote commitment"))).toBe(true);
  });
});
