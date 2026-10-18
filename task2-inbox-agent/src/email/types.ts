import { z } from "zod";

export const CATEGORIES = [
  "how_to",
  "troubleshooting",
  "project_request",
  "refund_cancellation",
  "complaint",
  "quote",
  "follow_up",
  "other",
] as const;

export type Category = (typeof CATEGORIES)[number];

export const RiskLevel = z.enum(["low", "medium", "high"]);
export type RiskLevel = z.infer<typeof RiskLevel>;

export const UrgencyLevel = z.enum(["low", "medium", "high", "critical"]);
export type UrgencyLevel = z.infer<typeof UrgencyLevel>;

export const EmailSchema = z.object({
  id: z.string(),
  subject: z.string(),
  sender: z.string(),
  received_at: z.string(),
  body: z.string(),
  expected_category: z.enum(CATEGORIES),
  subcategory: z.string(),
  risk: RiskLevel,
  key_facts: z.array(z.string()),
  expected_behavior: z.string(),
  expected_source: z.string().nullable().optional(),
  is_test_holdout: z.boolean().default(false),
});

export type EmailRecord = z.infer<typeof EmailSchema>;

export const ClassificationSchema = z.object({
  category: z.enum(CATEGORIES),
  subcategory: z.string(),
  urgency: UrgencyLevel,
  risk: RiskLevel,
  reasoning: z.string().optional(),
  confidence: z.number().min(0).max(1).default(0.9),
});

export type ClassificationResult = z.infer<typeof ClassificationSchema>;

export const DraftSchema = z.object({
  category: z.enum(CATEGORIES),
  summary: z.string(),
  reply: z.string(),
  sources: z.array(z.string()).default([]),
  risk: RiskLevel,
  needs_human: z.boolean(),
  next_action: z.string(),
  follow_up_date: z.string().nullable().optional(),
  prompt_version: z.string().default("drafting@v1"),
  knowledge_state: z.enum(["grounded", "insufficient_evidence", "knowledge_unavailable"]).default("grounded"),
});

export type DraftResult = z.infer<typeof DraftSchema>;

export const ReviewActionSchema = z.object({
  email_id: z.string(),
  action: z.enum(["approve_send", "edit_send", "reject_write_own", "escalate_expert"]),
  final_reply: z.string(),
  edit_reason: z.string().optional(),
  reviewer: z.string().default("Support Lead"),
});

export type ReviewAction = z.infer<typeof ReviewActionSchema>;
