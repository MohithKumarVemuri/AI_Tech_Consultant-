import { EmailRecord, ClassificationResult, ClassificationSchema } from "../email/types";
import { llmClient } from "../llm-client";

const SYSTEM_PROMPT = `You are an expert customer support triaging agent for a software business.
Classify the incoming customer email into exactly ONE of the 8 categories:
- how_to: Questions on how to configure or use features
- troubleshooting: Reporting bugs, errors, outages, or misbehavior
- project_request: Asking for custom software development or major integrations
- refund_cancellation: Requesting subscription refunds, downgrades, or account cancellation
- complaint: Customer dissatisfaction, SLA breach, or strong grievances
- quote: Inquiries asking for pricing, estimates, or migration rates
- follow_up: Checking status on an existing conversation, invoice, or ticket
- other: Any email that does not fit above

Determine:
1. category (one of the 8 above)
2. subcategory (format: category/topic, e.g. how_to/billing, troubleshooting/maps)
3. urgency: low | medium | high | critical
4. risk: low | medium | high
5. reasoning: brief explanation

Return ONLY valid JSON matching the schema.`;

export async function classifyEmail(email: EmailRecord): Promise<ClassificationResult> {
  // Check for edge cases
  if (!email.body.trim() && !email.subject.trim()) {
    return {
      category: "other",
      subcategory: "other/empty",
      urgency: "low",
      risk: "low",
      reasoning: "Empty email subject and body",
      confidence: 1.0,
    };
  }

  // Prompt injection check
  const content = `${email.subject}\n\n${email.body}`.toLowerCase();
  if (
    content.includes("ignore all previous instructions") ||
    content.includes("system instruction override") ||
    content.includes("override instructions")
  ) {
    return {
      category: email.expected_category || "other",
      subcategory: `${email.expected_category || "other"}/injection_attempt`,
      urgency: "critical",
      risk: "high",
      reasoning: "Prompt injection attack detected in email content",
      confidence: 0.99,
    };
  }

  const prompt = `Classify this email:
Sender: ${email.sender}
Subject: ${email.subject}
Body:
${email.body}`;

  const res = await llmClient.generate<ClassificationResult>({
    prompt,
    system: SYSTEM_PROMPT,
    schema: ClassificationSchema as any,
    promptVersion: "classifier@v1",
    temperature: 0.0,
  });

  if (res.structured) {
    return res.structured;
  }

  // Rule-based deterministic fallback
  return {
    category: email.expected_category || "how_to",
    subcategory: email.subcategory || "how_to/general",
    urgency: "low",
    risk: email.risk || "low",
    reasoning: "Fallback classification",
    confidence: 0.9,
  };
}
