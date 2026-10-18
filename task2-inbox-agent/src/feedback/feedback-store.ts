import fs from "fs";
import path from "path";

export interface FeedbackRecord {
  id: string;
  emailId: string;
  category: string;
  subcategory: string;
  originalDraft: string;
  finalReply: string;
  action: "approve_send" | "edit_send" | "reject_write_own" | "escalate_expert";
  editReason?: string;
  similarity: number;
  isUnchanged: boolean;
  reviewer: string;
  promptVersion: string;
  model: string;
  timestamp: string;
}

const STORE_PATH = path.resolve(process.cwd(), "data", "feedback_history.json");

function ensureStoreExists() {
  const dir = path.dirname(STORE_PATH);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
  if (!fs.existsSync(STORE_PATH)) {
    fs.writeFileSync(STORE_PATH, JSON.stringify([], null, 2), "utf-8");
  }
}

export function saveFeedback(record: FeedbackRecord): void {
  ensureStoreExists();
  try {
    const raw = fs.readFileSync(STORE_PATH, "utf-8");
    const list: FeedbackRecord[] = JSON.parse(raw);
    list.unshift(record);
    fs.writeFileSync(STORE_PATH, JSON.stringify(list, null, 2), "utf-8");
  } catch (err) {
    console.error("[FeedbackStore] Save failed:", err);
  }
}

export function getAllFeedback(): FeedbackRecord[] {
  ensureStoreExists();
  try {
    const raw = fs.readFileSync(STORE_PATH, "utf-8");
    return JSON.parse(raw);
  } catch {
    return [];
  }
}

export function getFeedbackForSubcategory(subcategory: string): FeedbackRecord[] {
  return getAllFeedback().filter((f) => f.subcategory === subcategory);
}
