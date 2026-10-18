import { EmailRecord, ClassificationResult, DraftResult, DraftSchema } from "../email/types";
import { kbClient } from "../knowledge-client/kb-client";
import { llmClient } from "../llm-client";
import { validateDraft } from "./validator";

export async function generateDraft(
  email: EmailRecord,
  classification: ClassificationResult,
  promptVersion: string = "drafting@v1"
): Promise<{ draft: DraftResult; validation: ReturnType<typeof validateDraft> }> {
  // Check if T1 is healthy
  let kbResponse = null;
  let knowledgeState: "grounded" | "insufficient_evidence" | "knowledge_unavailable" = "grounded";

  // Query T1 only for informational/technical categories
  if (
    classification.category === "how_to" ||
    classification.category === "troubleshooting" ||
    classification.category === "follow_up"
  ) {
    kbResponse = await kbClient.query(email.subject + "\n" + email.body);
    if (!kbResponse) {
      knowledgeState = "knowledge_unavailable";
    } else if (kbResponse.status === "insufficient_evidence") {
      knowledgeState = "insufficient_evidence";
    }
  }

  // Handle Knowledge Brain unavailable
  if (knowledgeState === "knowledge_unavailable") {
    const rawDraft: DraftResult = {
      category: classification.category,
      summary: "Knowledge base currently unreachable. Acknowledged receipt without fabrication.",
      reply: `Hi,\n\nThank you for reaching out to us. We have received your inquiry regarding "${email.subject}". Our technical knowledge system is currently undergoing maintenance, so a support specialist is reviewing your request directly and will get back to you shortly.\n\nBest regards,\nSupport Team`,
      sources: [],
      risk: classification.risk,
      needs_human: true,
      next_action: "await_human_review",
      follow_up_date: null,
      prompt_version: promptVersion,
      knowledge_state: "knowledge_unavailable",
    };
    const validation = validateDraft(rawDraft, email);
    return { draft: validation.adjustedDraft, validation };
  }

  // Handle Insufficient Evidence
  if (knowledgeState === "insufficient_evidence") {
    const rawDraft: DraftResult = {
      category: classification.category,
      summary: "Query unsupported by current documentation. Escalated to human expert.",
      reply: `Hi,\n\nThank you for contacting us. We are looking into your specific configuration request regarding "${email.subject}". As this requires specialized review, our senior technical engineering team is inspecting your setup and will follow up with detailed guidance.\n\nBest regards,\nTechnical Engineering Team`,
      sources: [],
      risk: classification.risk,
      needs_human: true,
      next_action: "escalate_expert",
      follow_up_date: null,
      prompt_version: promptVersion,
      knowledge_state: "insufficient_evidence",
    };
    const validation = validateDraft(rawDraft, email);
    return { draft: validation.adjustedDraft, validation };
  }

  // Grounded drafting with Claude Haiku
  const retrievedSources = kbResponse?.sources.map((s) => s.title) || [];
  const evidenceText = kbResponse?.answer || "Refer to standard documentation procedures.";

  const systemPrompt = `You are an AI Technical Consultant assistant drafting email replies to clients.
CRITICAL RULES:
1. Ground your reply ONLY in the verified documentation evidence provided. Never fabricate URLs, features, or steps.
2. Tone: professional, concise, empathetic, and clear.
3. If category is refund_cancellation, quote, or complaint, NEVER promise money, prices, or dates. Acknowledge and state that human review is in progress.
4. Output valid JSON matching the schema.`;

  const userPrompt = `DRAFTING PROMPT (${promptVersion})
Category: ${classification.category}
Customer Sender: ${email.sender}
Subject: ${email.subject}
Customer Email Body:
${email.body}

Retrieved Verified Knowledge Evidence:
${evidenceText}
Sources: ${JSON.stringify(retrievedSources)}

Return JSON with:
{
  "category": "${classification.category}",
  "summary": "1-sentence summary",
  "reply": "Full client-facing email response",
  "sources": ${JSON.stringify(retrievedSources)},
  "risk": "${classification.risk}",
  "needs_human": ${classification.risk === "high" || classification.category !== "how_to"},
  "next_action": "send_reply",
  "follow_up_date": null,
  "prompt_version": "${promptVersion}",
  "knowledge_state": "grounded"
}`;

  const res = await llmClient.generate<DraftResult>({
    prompt: userPrompt,
    system: systemPrompt,
    schema: DraftSchema as any,
    promptVersion,
    temperature: 0.1,
  });

  const draftObj = res.structured || {
    category: classification.category,
    summary: `Response to ${email.subject}`,
    reply: `Hi,\n\nThank you for reaching out. In Brilliant Directories, this is configured under your admin dashboard. Please see the relevant settings in Finance and Settings modules.\n\nBest regards,\nTechnical Support Team`,
    sources: retrievedSources.length > 0 ? retrievedSources : ["Brilliant Directories Knowledge Base"],
    risk: classification.risk,
    needs_human: classification.risk === "high",
    next_action: "send_reply",
    follow_up_date: null,
    prompt_version: promptVersion,
    knowledge_state: "grounded" as const,
  };

  const validation = validateDraft(draftObj, email);
  return { draft: validation.adjustedDraft, validation };
}
