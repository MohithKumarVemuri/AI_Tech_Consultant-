import fs from "fs";
import path from "path";
import os from "os";

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

const isServerless = !!(process.env.VERCEL || process.env.AWS_LAMBDA_FUNCTION_NAME);
const STORE_DIR = isServerless ? path.join(os.tmpdir(), "data") : path.resolve(process.cwd(), "data");
const STORE_PATH = path.join(STORE_DIR, "feedback_history.json");

// In-memory fallback for serverless / read-only filesystems
let memoryFeedback: FeedbackRecord[] = [];

function ensureStoreExists() {
  try {
    if (!fs.existsSync(STORE_DIR)) {
      fs.mkdirSync(STORE_DIR, { recursive: true });
    }
    if (!fs.existsSync(STORE_PATH)) {
      fs.writeFileSync(STORE_PATH, JSON.stringify([], null, 2), "utf-8");
    }
  } catch {
    // Read-only filesystem fallback
  }
}

export function saveFeedback(record: FeedbackRecord): void {
  memoryFeedback.unshift(record);
  try {
    ensureStoreExists();
    let list: FeedbackRecord[] = [];
    if (fs.existsSync(STORE_PATH)) {
      list = JSON.parse(fs.readFileSync(STORE_PATH, "utf-8"));
    }
    list.unshift(record);
    fs.writeFileSync(STORE_PATH, JSON.stringify(list, null, 2), "utf-8");
  } catch (err) {
    // In-memory array already holds the record
  }
}

export function getAllFeedback(): FeedbackRecord[] {
  try {
    ensureStoreExists();
    if (fs.existsSync(STORE_PATH)) {
      const diskList: FeedbackRecord[] = JSON.parse(fs.readFileSync(STORE_PATH, "utf-8"));
      return diskList.length > 0 ? diskList : memoryFeedback;
    }
  } catch {
    // fallback
  }
  return memoryFeedback;
}

export function getFeedbackForSubcategory(subcategory: string): FeedbackRecord[] {
  return getAllFeedback().filter((f) => f.subcategory === subcategory);
}
